"""Example script for running the core methods of the FuncX planner"""
from argparse import ArgumentParser
from pathlib import Path
from typing import Tuple

from sklearn.gaussian_process import GaussianProcessRegressor, kernels
from sklearn.feature_selection import VarianceThreshold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from modAL.acquisition import EI
from yaml import SafeLoader
import numpy as np
import yaml

from planner import run_inference
from polybot.models import Sample
from polybot.planning import OptimizationProblem


def fit_model(opt_spec: OptimizationProblem, train_x: np.ndarray, train_y: np.ndarray) -> Pipeline:
    """Fit and test a model using the latest data

    Args:
        opt_spec: Configuration file for the optimization
        train_x: Input columns
        train_y: Output column
        out_dir: Location to store the data
    """
    # Create an initial RBF kernel, using the training set mean as a scaling parameter
    kernel = train_y.mean() ** 2 * kernels.RBF(length_scale=1)

    # TODO (wardlt): Make it clear where featurization would appear, as we are soon to introduce additives
    #  This will yield chemical degrees of freedom better captured using features of the additives rather
    #  than a new variable per additive
    #  Notes for now: Mol. Weight, Side Chain Length, and ... are the likely candidates

    # Add a noise parameter based on user settings
    noise = opt_spec.planner_options.get('noise_level', 0)
    if noise < 0:
        # Use standard deviation of the distribution of train_y will be the estimation of initial noise
        # TODO (wardlt): Document where 3, 4, and 11 come from
        noise_estimated = np.std(train_y) / 3
        noise_lb = noise_estimated / 4
        noise_ub = noise_estimated * 11

        kernel_noise = kernels.WhiteKernel(noise_level=noise_estimated ** 2,
                                           noise_level_bounds=(noise_lb ** 2, noise_ub ** 2))
        kernel = kernel + kernel_noise
    elif noise > 0:
        kernel = kernel + kernels.WhiteKernel(noise ** 2, noise_level_bounds=(noise ** 2,) * 2)

    # Train a GPR model
    model = Pipeline([
        ('variance', VarianceThreshold()),
        ('scale', StandardScaler()),
        ('gpr', GaussianProcessRegressor(kernel))
    ])

    # Train and save the model
    model.fit(train_x, train_y)
    print(f'Finished fitting the model on {len(train_x)} data points')
    print(f'Optimized model: {model["gpr"].kernel_}')
    return model


def generate_training_set(opt_spec: OptimizationProblem, sample_path) -> Tuple[np.ndarray, np.ndarray]:
    """Load in all of the previous samples to build a training set

    Uses the inputs and outputs defined in the optimization specification

    Returns:
        - Input features
        - Output variable
    """

    # Get the name of the input columns
    input_columns = opt_spec.search_template.input_columns

    train_x = []
    train_y = []
    # Loop over samples in the training data
    for path in Path(sample_path).rglob('*.json'):
        sample = Sample.parse_file(path)
        train_x.append([sample.inputs[c] for c in input_columns])  # Get only the needed input columns
        train_y.append(sample.processed_output[opt_spec.output])  # Get the target output column

    # Convert them to numpy and return
    return np.array(train_x), np.array(train_y)


if __name__ == "__main__":
    # Make some CLI arguments
    parser = ArgumentParser()
    parser.add_argument('--train-files', help='Path to the completed samples', default='samples')
    parser.add_argument('--optimization-spec', help='Configuration file', default='opt_spec.yaml')
    args = parser.parse_args()

    # Load in the optimization configuration
    with open(args.optimization_spec) as fp:
        opt_spec = yaml.load(fp, Loader=SafeLoader)
    opt_spec = OptimizationProblem.parse_obj(opt_spec)

    # Get the training data
    train_x, train_y = generate_training_set(opt_spec, args.train_files)
    print(f'Loaded a training set of {len(train_x)} entries')

    # Log-normalize conductivity
    train_y = np.log(train_y)

    # Fit a model and save the training records
    model = fit_model(opt_spec, train_x, train_y)

    # Create the search space
    possible_options = opt_spec.search_template.generate_search_space_dataframe()
    search_x = possible_options[opt_spec.search_template.input_columns]
    print(f'Created {len(search_x)} samples to be evaluated')

    # Perform the inference
    # TODO (wardlt): This is the part that can be parallelized
    chunk_size = opt_spec.planner_options.get('chunk_size')
    search_y = []
    search_std = []
    for chunk in np.array_split(search_x, len(search_x) // chunk_size):
        y_pred, y_std = run_inference(model, chunk)
        search_y.append(y_pred)
        search_std.append(y_std)
    search_y = np.vstack(search_y)
    search_std = np.vstack(search_std)

    # Get the largest UCB
    assert opt_spec.maximize, "The optimization requests minimization"
    ei = EI(search_y, search_std, max_val=np.max(train_y), tradeoff=0.1)
    best_ind = np.argmax(ei)
    best_point = search_x.iloc[best_ind][opt_spec.search_template.input_columns]

    # Make the sample and save it to disk
    output = opt_spec.search_template.create_new_sample()
    for p, x in zip(opt_spec.search_template.input_columns, best_point):
        output.inputs[p] = x
    with open('next_sample.json', 'w') as fp:
        fp.write(output.json(indent=2))
