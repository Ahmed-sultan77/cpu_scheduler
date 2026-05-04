# metrics/__init__.py
from metrics.calculator import calculate, AlgorithmResult
from metrics.comparison import compare, ComparisonReport

__all__ = ["calculate", "AlgorithmResult", "compare", "ComparisonReport"]