"""Collects the pycuber validation gate (tools/validate_moves.py) into the
test suite. That module can still be run on its own; importing its test class
and autouse fixture here makes `python -m pytest -m slow` (and `-m ""`) run
it too, instead of leaving the engine's reference check outside testpaths.
"""

from tools.validate_moves import TestValidateMoves, setup_engine  # noqa: F401
