"""Shared completion predicates for weekly simulation control."""


def is_weekly_simulation_complete(day: int, total_days: int, step_days: int = 7) -> bool:
    """Return True when another full weekly step would exceed ``total_days``.

    The engine advances through ``/next-week`` in fixed-size weekly steps. For
    totals that are not exact multiples of seven, the last valid terminal day is
    therefore the final day from which another full week would overshoot the
    configured session limit.
    """
    return total_days > 0 and day + step_days > total_days
