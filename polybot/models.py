"""Data models for objects used by this service"""
from typing import List, Dict, Any, Optional, Tuple, Iterable, Union
from itertools import product
from uuid import uuid4

from pydantic import BaseModel, Field
import pandas as pd
import numpy as np


class Sample(BaseModel):
    """Description for a UVVis experiment"""

    # Sample identifiers
    ID: str = Field(default_factory=lambda: uuid4().hex[-10:],
                    description="Unique identifier for this sample used across robotic systems",
                    regex=r'[0-9a-f]{10}')
    score: Optional[float] = Field(None, description='Priority for evaluating the sample. Higher will run sooner')

    # State information
    status: str = Field(None, description="Status of the sample")
    timestamp: List[str] = Field(default_factory=list, description='List of times sample object was modified')

    # Workflow information
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Inputs to the system workflow")

    # Output data
    raw_output: Dict[str, Any] = Field(default_factory=dict, description="Data as recorded on an instrument")
    processed_output: Dict[str, Any] = Field(default_factory=dict,
                                             description="Summarized or post-processed versions of raw data")

    def reset_id(self):
        """Generate a new sample ID"""
        uuid = uuid4()
        self.ID = uuid.hex[-10:]

    class Config:
        extra = 'allow'


class SampleTemplate(Sample):
    """Description for how to create new samples. Includes the parameters for the workflow file,
    human-readable descriptions and the ranges over which they are allowed to vary.

    A superset of the information held by a :class:`Sample` object.
    """

    ID: Optional[str] = None

    inputs_info: Dict[str, str] = Field(default_factory=dict, help='Human-readable descriptions of each parameter')

    inputs_space: Dict[str, Optional[Tuple[float, float, float]]] = Field(
        default_factory=dict, help='Allowed ranges and values of the different input parameters. '
                                   'Tuples specify the minimum, maximum, and step size. '
                                   'Null values indicate parameters that must remain their default values'
    )
    inputs_interval: Dict[str, str] = Field(
        default_factory=dict, help='Defines whether the range in inputs_space is inclusive or not, '
                                   'or whether the value should be held constant',
        regex=r'^(\[constant\]|[\(\[][0-9.]+,\s*[0-9.][0-9.]+[\)\]])$'
    )
    inputs_dtype: Dict[str, str] = Field(
        default_factory=dict, help='The numerical type of the value of a field'
    )

    @property
    def input_columns(self) -> List[str]:
        """Name of the input columns to the optimization algorithm

        Always returns the columns in the same order
        """
        return sorted(self.inputs.keys())

    def create_new_sample(self) -> Sample:
        """Get an template for a new sample

        Returns:
            A new sample instance
        """
        return Sample(**self.dict(exclude={'_inputs_info', 'inputs_space', 'ID'}))

    def generate_search_space(self) -> Iterable[Dict[str, Any]]:
        """Generate the inputs for all possible values of the new samples

        Yields:
            Dictionary of inputs for each step
        """

        # Get a list of input fields and a second list of acceptable values
        acceptable_inputs = self.list_acceptable_input_values()
        keys, acceptable_values = zip(*acceptable_inputs.items())

        # Use itertools to generate the full range
        for vals in product(*acceptable_values):
            yield dict(zip(keys, vals))

    def get_acceptable_values_for_field(self, field: str) -> List[Union[int, float]]:
        """Get a list of acceptable values for a specific field

        Args:
            field: Name of the field
        Returns:
            List of acceptable values
        """

        assert field in self.inputs_interval, f"Field \"{field}\" does not have a defined interval"
        assert field in self.inputs_dtype, f"Field \"{field}\" does not have a defined units"

        if self.inputs_space[field] is None:
            assert self.inputs_interval[field] == "[constant]",\
                "Inconsistent template: Space is null and interval is not [constant]"
            return [self.inputs[field]]
        else:
            assert self.inputs_interval[field] != "[constant]", \
                "Inconsistent template: Space is not null and interval is [constant]"

            # TODO: We ignore the values in "interval" and assume they are consistent with input_space
            _min, _max, _step = self.inputs_space[field]
            vals = np.arange(_min, _max + _step, _step,  # _max + _step makes the range inclusive
                             dtype=self.inputs_dtype[field])

            # Prune off the first and last entry if they are exclusive
            if self.inputs_interval[field].startswith("("):
                vals = vals[1:]
            if self.inputs_interval[field].endswith(")"):
                vals = vals[:-1]
            return vals

    def list_acceptable_input_values(self) -> Dict[str, List[float]]:
        """Get the possible options for each input

        Returns:
            Dictionary where keys are the name of an input field and values are
            a list of acceptable values for that field
        """
        # Loop over the input space and get the possible values for each input
        return dict((key, self.get_acceptable_values_for_field(key))
                    for key in self.inputs_space)

    def generate_search_space_dataframe(self) -> pd.DataFrame:
        """Create the search space as a Pandas DataFrame"""
        return pd.DataFrame(list(self.generate_search_space()))
