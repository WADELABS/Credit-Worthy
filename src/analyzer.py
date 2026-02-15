"""
src/analyzer.py
Comprehensive analysis for credit utilization and payment recommendations.
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

    def calculate_utilization(self, transactions: List[Dict[str, Any]], credit_limit: float) -> Dict[str, Any]:
        """
        Calculates the current utilization rate based on transactions and limit.
        """
        total_spent = sum(t.get("amount", 0) for t in transactions if t.get("type") == "purchase")
        total_paid = sum(t.get("amount", 0) for t in transactions if t.get("type") == "payment")
        
        balance = total_spent - total_paid
        utilization_rate = balance / credit_limit if credit_limit > 0 else 0
        
        return {
            "balance": balance,
            "utilization_rate": round(utilization_rate, 2),
            "status": "warning" if utilization_rate > self.alert_threshold else "healthy"
        }

    def get_payment_suggestion(self, balance: float, credit_limit: float) -> str:
        """
        Suggests a payment amount to keep utilization healthy.
        """
        utilization = balance / credit_limit if credit_limit > 0 else 0
        if utilization > self.alert_threshold:
            # Calculate amount needed to get down to 30% (standard healthy rate)
            target_balance = credit_limit * 0.3
            suggested_payment = balance - target_balance
            return f"Suggested payment: ${round(suggested_payment, 2)} to reach 30% utilization."
        return "Utilization is healthy. Pay at least the minimum."

    def score_transaction(self, transaction: Dict[str, Any]) -> float:
        """
        Provides a score indicating the priority of a transaction.
        """
        amount = transaction.get("amount", 0)
        if amount > 1000:
            return 0.9
        elif amount > 500:
            return 0.5
        return 0.1
