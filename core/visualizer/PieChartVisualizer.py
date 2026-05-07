import matplotlib.pyplot as plt

from matplotlib.figure import Figure
from typing import Dict

from core.visualizer.ChartFactory import ChartFactory

class PieChartVisualizer(ChartFactory):
    def render(self, data_dict: Dict[str, Dict[str, float]], title: str = "") -> Figure:
        fig = Figure(figsize=(4, 3), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)

        if not data_dict:
            ax.text(0.5, 0.5, "No Data", ha='center', va='center', color='#767676')
            ax.set_axis_off()
            return fig

        total_income = sum(p.get('Income', 0) for p in data_dict.values())
        total_expense = sum(p.get('Expense', 0) for p in data_dict.values())
        total_bal = sum(max(0, p.get('Total Balance', 0)) for p in data_dict.values())

        raw_labels = ['Income', 'Expense', 'Total Balance']
        raw_values = [total_income, total_expense, total_bal]

        # Filter out zero/negative values
        labels = []
        values = []
        for l, v in zip(raw_labels, raw_values):
            if v > 0:
                labels.append(l)
                values.append(v)

        if not values:
            ax.text(0.5, 0.5, "No positive assets", ha='center', va='center', color='#767676')
            ax.set_axis_off()
            return fig

        total_sum = sum(values)

        # Combine Label
        final_labels = []
        for l, v in zip(labels, values):
            pct = (v / total_sum) * 100
            final_labels.append(f"{l}\n${v:,.0f}\n({pct:.1f}%)")

        color_map = {'Income': '#004a99', 'Expense': '#D22E1E', 'Total Balance': '#00d2ff'}
        colors = [color_map[l] for l in labels]

        # Create the pie chart
        wedges, texts = ax.pie(
            values,
            labels=final_labels,
            startangle=90,
            colors=colors,
            labeldistance=1.15,  # Pushes labels further out to avoid crowding
            wedgeprops={'width': 0.4, 'edgecolor': 'white'}
        )

        # Style the outer label text
        plt.setp(texts, size=9, color="#333333", fontweight='bold')

        ax.set_title(title, fontsize=12, fontweight='bold', pad=20, color='#004879')
        fig.tight_layout()

        return fig