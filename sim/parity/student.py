"""Learner-owned core: the conductor must not complete this TODO."""
from __future__ import annotations

from collections.abc import Sequence


def gain_schedule(
    coefficients: Sequence[Sequence[float]], leg_length_m: float,
) -> list[list[float]]:
    """Return a 2x6 matrix: wheel gains first, then virtual hip torque gains.

    Input: 12 coefficient rows, four values per row in [a3, a2, a1, a0]
    order; leg_length_m is in meters. Each row represents a cubic.

    TODO (you): evaluate each row at the supplied length, preserve row order,
    and arrange the 12 results into two rows of six. Return numbers, not
    strings. The test runner supplies validated inputs and checks outputs.

    Do not add a minus sign, clamp lengths or change coefficient order:
    this exercise reproduces a gain schedule, not the feedback command.
    No NumPy dependency is required. Do not call the C reference here.
    """
    raise NotImplementedError("Your exercise: implement gain_schedule in student.py")
