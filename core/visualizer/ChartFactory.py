from abc import ABC, abstractmethod
from typing import Dict
from matplotlib.figure import Figure

class ChartFactory(ABC):
    """Abstract base class for all chart visualizers"""

    @abstractmethod
    def render(self, data_dict: Dict[str, Dict[str, float]], title: str = "") -> Figure:
        """
        Processes multi-series data.
        Expected format: {'Period1': {'Income': 100, 'Expense': 50, 'Balance': 50}, ...}
        """
        pass