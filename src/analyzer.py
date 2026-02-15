"""
src/analyzer.py
Calculates credit utilization and evaluates transaction patterns.
"""

from typing import Dict, List, Any

class CreditAnalyzer:
    """
    Analyzes credit data to provide utilization metrics and risk scores.
    """
    def __init__(self, alert_threshold: float = 0.7):
        """
        Initializes the analyzer with a specific alert threshold.
        """
        self.alert_threshold = alert_threshold

    def calculate_utilization(self, transactions: List[Dict[str, Any]], limit: float) -> Dict[str, Any]:
        """
        Calculates the current utilization rate based on a list of transactions.
        """
        total_balance = sum(t.get("amount", 0) for t in transactions if t.get("type") == "purchase")
        total_payments = sum(t.get("amount", 0) for t in transactions if t.get("type") == "payment")
        
        current_balance = total_balance - total_payments
        utilization_rate = current_balance / limit if limit > 0 else 0
        
        return {
            "balance": current_balance,
            "utilization_rate": round(utilization_rate, 2),
            "status": "warning" if utilization_rate > self.alert_threshold else "healthy"
        }

    def score_transaction(self, transaction: Dict[str, Any]) -> float:
        """
        Provides a score (0 to 1) indicating the importance of a single transaction.
        """
        amount = transaction.get("amount", 0)
        if amount > 1000:
            return 0.9
        elif amount > 500:
            return 0.5
        return 0.1
