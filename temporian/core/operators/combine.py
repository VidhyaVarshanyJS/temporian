# Copyright 2021 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Combine operator class and public API function definitions."""

from temporian.core import operator_lib
from temporian.core.compilation import compile
from temporian.core.data.node import (
    EventSetNode,
    create_node_new_features_new_sampling,
)
from temporian.core.operators.base import Operator
from temporian.core.typing import EventSetOrNode
from temporian.proto import core_pb2 as pb
from temporian.utils.rtcheck import rtcheck

MAX_NUM_ARGUMENTS = 30


class Combine(Operator):
    def __init__(self, **inputs: EventSetNode):
        super().__init__()

        # Note: Support for dictionaries of nodes is required for
        # serialization.

        if len(inputs) < 2:
            raise ValueError("At least two arguments should be provided")

        if len(inputs) >= MAX_NUM_ARGUMENTS:
            raise ValueError(
                f"Too many (>{MAX_NUM_ARGUMENTS}) arguments provided"
            )

        # inputs
        first_input = None
        all_unix_timestamp = True
        for key, input in inputs.items():
            # Check that all features are in all nodes
            if first_input is None:
                first_input = input
            first_input.schema.check_compatible_features(
                input.schema, check_order=False
            )

            # Output is unix if all inputs are
            all_unix_timestamp &= input.schema.is_unix_timestamp
            self.add_input(key, input)

        assert first_input is not None  # for static checker
        self.add_output(
            "output",
            create_node_new_features_new_sampling(
                features=first_input.schema.features,
                indexes=first_input.indexes,
                is_unix_timestamp=all_unix_timestamp,
                creator=self,
            ),
        )
        self.check()

    @classmethod
    def build_op_definition(cls) -> pb.OperatorDef:
        return pb.OperatorDef(
            key="COMBINE",
            inputs=[
                pb.OperatorDef.Input(key=f"input_{idx}", is_optional=idx >= 2)
                for idx in range(MAX_NUM_ARGUMENTS)
            ],
            outputs=[pb.OperatorDef.Output(key="output")],
        )


operator_lib.register_operator(Combine)


@rtcheck
@compile
def combine(
    *inputs: EventSetOrNode,
) -> EventSetOrNode:
    """Combines all events from multiple EventSets with the same features and index.

    Input events must have the same feature names and dtypes, and the order of the first
    input's features is used for the output feature list.

    Since the input timestamps may overlap at some points, the result may contain
    multiple events for the same timestamp. Duplicated events are not unified or
    aggregated in any way.
    Check the second part of the example below to see how to unify
    events with the same timestamp, in this case adding their values.

    If all inputs contain unix timestamps (i.e., datetimes), the output will also
    be unix timestamps.

    Args:
        *inputs: EventSets to combine their events.

    Example combining duplicated timestamps:

        ```python
        >>> a = tp.event_set(timestamps=[0, 1, 3],
        ...                  features={"A": [0, 10, 30], "B": [0, -10, -30]}
        ...                 )
        >>> b = tp.event_set(timestamps=[1, 4],
        ...                  features={"B": [-10, -40], "A": [10, 40]}
        ...                 )
        >>> c = tp.combine(a, b)
        >>> c
        indexes: []
        features: [('A', int64), ('B', int64)]
        events:
            (5 events):
                timestamps: [0. 1. 1. 3. 4.]
                'A': [ 0 10 10 30 40]
                'B': [ 0 -10 -10 -30 -40]
        ...

        >>> # Unify events with the same timestamp (add their values).
        >>> unique_t = c.unique_timestamps()
        >>> d = c.moving_sum(window_length=0, sampling=unique_t)
        indexes: []
        features: [('A', int64), ('B', int64)]
        events:
            (4 events):
                timestamps: [0. 1. 3. 4.]
                'A': [ 0 20 30 40]
                'B': [ 0 -20 -30 -40]
        ...

        ```


    Returns:
        An EventSet with events from all inputs combined.
    """
    if len(inputs) == 1:
        return inputs[0]

    return Combine(inputs).outputs["output"]  # type: ignore
