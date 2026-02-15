"""
src/heuristics.py
Core heuristic engine for optimizing capital utilization.
"""

from typing import Dict, Any

class UtilizationHeuristic:
    """
    Evaluates credit utilization and provides aggression scores.
    """
    def __init__(self, aggression_threshold: float = 0.7):
        """
        Initializes the heuristic engine with a specific aggression threshold.
        
        Args:
            aggression_threshold (float): Sensitivity to utilization spikes (0.0 to 1.0).
        """
        self.aggression_threshold = aggression_threshold

    def evaluate(self, transaction: Dict[str, Any]) -> float:
        """
        Evaluates a transaction for its impact on capital utilization.
        
        Returns:
            float: A veracity/aggression score where higher values trigger optimization alerts.
        """
        amount = transaction.get("amount", 0)
        # Simplified scoring logic for portfolio demonstration
        if amount > 1000:
            return 0.9
        elif amount > 500:
            return 0.5
        return 0.1
