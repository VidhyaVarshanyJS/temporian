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

from datetime import datetime

from temporian.core.operators.calendar.iso_week import (
    CalendarISOWeekOperator,
)
from temporian.implementation.numpy import implementation_lib
from temporian.implementation.numpy.operators.calendar.base import (
    BaseCalendarNumpyImplementation,
)


class CalendarISOWeekNumpyImplementation(BaseCalendarNumpyImplementation):
    """Numpy implementation of the calendar_iso_week operator."""

    def __init__(self, operator: CalendarISOWeekOperator) -> None:
        super().__init__(operator)

    def _get_value_from_datetime(self, dt: datetime) -> int:
        return dt.isocalendar()[1]


implementation_lib.register_operator_implementation(
    CalendarISOWeekOperator, CalendarISOWeekNumpyImplementation
)
