import numpy as np

from matplotlib.figure import Figure
from typing import Dict

from core.visualizer.ChartFactory import ChartFactory

class BarGraphVisualizer(ChartFactory):
    def render(self, data_dict: Dict[str, Dict[str, float]], title: str = "") -> Figure:
        fig = Figure(figsize=(6, 4), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)

        if not data_dict:
            ax.text(0.5, 0.5, "No Data", ha='center', va='center', color='#767676')
            ax.set_axis_off()
            return fig

        labels = list(data_dict.keys())
        income = [data_dict[l].get('Income', 0) for l in labels]
        expense = [data_dict[l].get('Expense', 0) for l in labels]
        balance = [data_dict[l].get('Total Balance', 0) for l in labels]

        x = np.arange(len(labels))
        width = 0.25

        ax.bar(x - width, income, width, label='Income', color='#004a99')
        ax.bar(x, expense, width, label='Expense', color='#D22E1E')
        ax.bar(x + width, balance, width, label='Total Balance', color='#00d2ff')

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')

        ax.set_title(title, fontsize=12, fontweight='bold', pad=15, color='#004879')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=9, color='#333333')

        ax.yaxis.grid(True, linestyle='--', alpha=0.3)
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=8, frameon=False)
        fig.tight_layout()

        return fig