"""
src/heuristics.py
Core heuristic engine for optimizing capital utilization.
"""

from typing import Dict, Any

class UtilizationHeuristic:
    """
    Evaluates credit utilization and provides aggression scores.
    """
    def __init__(self, alert_threshold: float = 0.7):
        """
        Initializes the logic engine with a specific alert threshold.
        
        Args:
            alert_threshold (float): Sensitivity to balance increases (0.0 to 1.0).
        """
        self.alert_threshold = alert_threshold

    def evaluate(self, transaction: Dict[str, Any]) -> float:
        """
        Evaluates a transaction for its impact on account balance.
        
        Returns:
            float: A score where higher values indicate the need for a payment alert.
        """
        amount = transaction.get("amount", 0)
        # Simplified scoring logic for portfolio demonstration
        if amount > 1000:
            return 0.9
        elif amount > 500:
            return 0.5
        return 0.1
