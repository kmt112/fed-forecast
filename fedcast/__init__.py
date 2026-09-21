"""FedCast: process-judged FOMC decision forecaster."""

# Outcome buckets for the next-meeting decision, in basis points, dovish -> hawkish.
OUTCOMES_BP: tuple[int, ...] = (-50, -25, 0, 25, 50)
