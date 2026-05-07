from matplotlib.figure import Figure
from typing import Dict

from core.visualizer.ChartFactory import ChartFactory

class LineGraphVisualizer(ChartFactory):
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

        ax.plot(labels, income, color='#004a99', linewidth=2, marker='o', label='Income')
        ax.plot(labels, expense, color='#D22E1E', linewidth=2, marker='o', label='Expense')
        ax.plot(labels, balance, color='#00d2ff', linewidth=2, marker='o', label='Total Balance')

        ax.fill_between(labels, balance, color='#00d2ff', alpha=0.1)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')

        ax.set_title(title, fontsize=12, fontweight='bold', pad=15, color='#004879')
        ax.tick_params(axis='x', rotation=30, labelsize=9, colors='#333333')
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=8, frameon=False)
        fig.tight_layout()

        return fig