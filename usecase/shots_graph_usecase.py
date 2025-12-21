"""
App name: Quantum Computing Simulation
Description: Usecase class for generating visualization graphs for measurement shots.
             This module does not connect to the database directly.
"""

import base64
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server-side rendering
import matplotlib.pyplot as plt
import numpy as np

from utils.logger import logger


class ShotsGraphUsecase:
    """
    A usecase class responsible for generating visualization graphs
    for quantum measurement shots. Does not connect to the database.
    """

    # Dark theme colors to match the app's UI
    COLORS = {
        'background': '#1a1a2e',
        'text': '#e0e0e0',
        'grid': '#333355',
        'bar_0': '#4a90d9',  # Blue for |0⟩
        'bar_1': '#d94a4a',  # Red for |1⟩
        'edge': '#ffffff'
    }

    def __init__(self):
        pass

    def generate_histogram(self, shot_data: list, sim_id: int = None, 
                           state_symbol: str = None, gate_symbol: str = None) -> dict:
        """
        Generate a bar chart histogram showing the distribution of measurement outcomes.
        
        Args:
            shot_data: List of shot dictionaries with 'outputState' field (0 or 1)
            sim_id: Simulation ID for the title (optional)
            state_symbol: State symbol for the title (e.g., '|0>')
            gate_symbol: Gate symbol for the title (e.g., '|H|')
        
        Returns:
            Dictionary with 'image' (base64 PNG) and 'interpretation' (text)
        """
        logger.info("START ShotsGraphUsecase.generate_histogram")

        # Count outcomes
        count_0 = sum(1 for shot in shot_data if shot.get('outputState') == 0)
        count_1 = sum(1 for shot in shot_data if shot.get('outputState') == 1)
        total = count_0 + count_1

        # Calculate percentages
        pct_0 = (count_0 / total * 100) if total > 0 else 0
        pct_1 = (count_1 / total * 100) if total > 0 else 0

        # Create figure with dark theme
        fig, ax = plt.subplots(figsize=(8, 5), facecolor=self.COLORS['background'])
        ax.set_facecolor(self.COLORS['background'])

        # Bar chart data
        states = ['|0⟩', '|1⟩']
        counts = [count_0, count_1]
        colors = [self.COLORS['bar_0'], self.COLORS['bar_1']]

        # Create bars
        bars = ax.bar(states, counts, color=colors, edgecolor=self.COLORS['edge'], linewidth=1.5, width=0.5)

        # Add percentage labels on bars
        for bar, count, pct in zip(bars, counts, [pct_0, pct_1]):
            height = bar.get_height()
            ax.annotate(
                f'{pct:.1f}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 5),
                textcoords="offset points",
                ha='center', va='bottom',
                color=self.COLORS['text'],
                fontsize=14,
                fontweight='bold'
            )

        # Build title with simulation details
        if sim_id and state_symbol and gate_symbol:
            title = f'Simulation {sim_id}: {state_symbol} State, {gate_symbol} Gate'
        elif sim_id:
            title = f'Simulation {sim_id}'
        else:
            title = 'Measurement Results'
        
        ax.set_title(title, color=self.COLORS['text'], fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('Output State', color=self.COLORS['text'], fontsize=12)
        ax.set_ylabel('Count', color=self.COLORS['text'], fontsize=12)

        # Set y-axis to start from 0 and have some headroom
        ax.set_ylim(0, max(counts) * 1.25 if max(counts) > 0 else 10)

        # Style ticks
        ax.tick_params(axis='x', colors=self.COLORS['text'], labelsize=14)
        ax.tick_params(axis='y', colors=self.COLORS['text'], labelsize=10)

        # Style spines
        for spine in ax.spines.values():
            spine.set_color(self.COLORS['grid'])

        # Add grid
        ax.yaxis.grid(True, color=self.COLORS['grid'], linestyle='--', alpha=0.5)
        ax.set_axisbelow(True)

        # Add total shots annotation
        ax.text(
            0.98, 0.98, f'Total Shots: {total}',
            transform=ax.transAxes,
            ha='right', va='top',
            color=self.COLORS['text'],
            fontsize=10,
            bbox=dict(boxstyle='round', facecolor=self.COLORS['grid'], alpha=0.8)
        )

        plt.tight_layout()

        # Convert to base64
        img_base64 = self._fig_to_base64(fig)
        plt.close(fig)

        # Generate interpretation
        interpretation = self._generate_interpretation(pct_0, pct_1, total)

        logger.info("END ShotsGraphUsecase.generate_histogram")
        return {
            'image': img_base64,
            'interpretation': interpretation
        }

    def generate_placeholder(self) -> dict:
        """
        Generate a placeholder graph when no simulation is selected.
        
        Returns:
            Dictionary with 'image' (base64 PNG) and 'interpretation' (empty string)
        """
        logger.info("START ShotsGraphUsecase.generate_placeholder")

        # Create figure with dark theme
        fig, ax = plt.subplots(figsize=(8, 5), facecolor=self.COLORS['background'])
        ax.set_facecolor(self.COLORS['background'])

        # Empty bar chart
        states = ['|0⟩', '|1⟩']
        counts = [0, 0]
        colors = [self.COLORS['bar_0'], self.COLORS['bar_1']]

        # Create empty bars with low alpha
        bars = ax.bar(states, counts, color=colors, edgecolor=self.COLORS['edge'], 
                      linewidth=1.5, width=0.5, alpha=0.3)

        # Styling
        ax.set_title('Measurement Results', color=self.COLORS['text'], fontsize=14, 
                     fontweight='bold', pad=15, alpha=0.5)
        ax.set_xlabel('Output State', color=self.COLORS['text'], fontsize=12, alpha=0.5)
        ax.set_ylabel('Count', color=self.COLORS['text'], fontsize=12, alpha=0.5)

        # Set y-axis
        ax.set_ylim(0, 10)

        # Style ticks
        ax.tick_params(axis='x', colors=self.COLORS['text'], labelsize=14)
        ax.tick_params(axis='y', colors=self.COLORS['text'], labelsize=10)

        # Style spines
        for spine in ax.spines.values():
            spine.set_color(self.COLORS['grid'])

        # Add grid
        ax.yaxis.grid(True, color=self.COLORS['grid'], linestyle='--', alpha=0.3)
        ax.set_axisbelow(True)

        # Add message
        ax.text(
            0.5, 0.5, 'Select a simulation to view results',
            transform=ax.transAxes,
            ha='center', va='center',
            color=self.COLORS['text'],
            fontsize=14,
            alpha=0.7,
            bbox=dict(boxstyle='round', facecolor=self.COLORS['grid'], alpha=0.8)
        )

        plt.tight_layout()

        # Convert to base64
        img_base64 = self._fig_to_base64(fig)
        plt.close(fig)

        logger.info("END ShotsGraphUsecase.generate_placeholder")
        return {
            'image': img_base64,
            'interpretation': ''
        }

    def _generate_interpretation(self, pct_0: float, pct_1: float, total: int) -> str:
        """
        Generate a human-readable interpretation of the measurement results.
        
        Args:
            pct_0: Percentage of |0⟩ outcomes
            pct_1: Percentage of |1⟩ outcomes
            total: Total number of shots
        
        Returns:
            Interpretation text string
        """
        # Determine the dominant outcome
        if abs(pct_0 - pct_1) < 5:
            distribution = "an approximately equal superposition"
            outcome_desc = f"roughly equal probability of measuring either |0⟩ or |1⟩"
        elif pct_0 > pct_1:
            if pct_0 > 90:
                distribution = "strongly biased toward |0⟩"
                outcome_desc = f"a high probability ({pct_0:.1f}%) of collapsing to the |0⟩ state"
            else:
                distribution = "biased toward |0⟩"
                outcome_desc = f"a higher probability ({pct_0:.1f}%) of measuring |0⟩ than |1⟩ ({pct_1:.1f}%)"
        else:
            if pct_1 > 90:
                distribution = "strongly biased toward |1⟩"
                outcome_desc = f"a high probability ({pct_1:.1f}%) of collapsing to the |1⟩ state"
            else:
                distribution = "biased toward |1⟩"
                outcome_desc = f"a higher probability ({pct_1:.1f}%) of measuring |1⟩ than |0⟩ ({pct_0:.1f}%)"

        interpretation = (
            f"This simulation ran {total} measurement shots. "
            f"The results show {distribution}, indicating {outcome_desc}. "
            f"In quantum mechanics, each measurement causes the qubit's superposition to collapse "
            f"into one of the basis states (|0⟩ or |1⟩), with probabilities determined by the "
            f"amplitudes of the quantum state after the gate operation."
        )
        
        return interpretation

    def _fig_to_base64(self, fig) -> str:
        """
        Convert a matplotlib figure to a base64-encoded PNG string.
        
        Args:
            fig: matplotlib Figure object
        
        Returns:
            Base64-encoded string (without data URI prefix)
        """
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                    facecolor=fig.get_facecolor(), edgecolor='none')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        return img_base64