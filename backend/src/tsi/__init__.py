"""The Swann Index (TSI): college football ratings, predictions, and book."""

import os

# Our linear algebra is many small (~300x300) solves. A multithreaded BLAS spends more
# time coordinating threads than computing: one thread is ~40x faster here. Must run
# before numpy is first imported; an explicit environment setting still wins.
for _var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

from importlib.metadata import version  # noqa: E402

__version__ = version("tsi")
