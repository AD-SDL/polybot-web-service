"""Example script for running the core methods of the FuncX planner"""

from argparse import ArgumentParser

from sklearn.gaussian_process import GaussianProcessRegressor
from tqdm import tqdm
import numpy as np

from planner import run_inference

if __name__ == "__main__":
    # Make some CLI arguments
    parser = ArgumentParser()
    parser.add_argument('--train-size', help='Number of points to use in the training set', default=32, type=int)
    parser.add_argument('--search-size', help='Number of points to generate in the search space',
                        default=1000000, type=int)
    parser.add_argument('--chunk-size', help='Number of points per inference chunk', default=16384)
    args = parser.parse_args()

    # Make the model
    n_dim = 8
    train_X = np.random.uniform(1, size=(args.train_size, n_dim))
    train_y = np.random.uniform(1, size=(args.train_size,))
    model = GaussianProcessRegressor()
    model.fit(train_X, train_y)
    print(f'Trained a model using a dataset with shape {train_X.shape}')

    # Run inference
    search_X = np.random.uniform(1, size=(args.search_size, n_dim))
    for chunk in tqdm(np.array_split(search_X, search_X.shape[0] // args.chunk_size)):
        run_inference(model, chunk)
