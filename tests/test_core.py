import pytest
from src.analyzer import CreditAnalyzer

def test_can_calculate_credit_usage():
    """Check if the math works on sample transactions"""
    analyzer = CreditAnalyzer()
    test_data = [
        {"amount": 500, "type": "purchase"},
        {"amount": 200, "type": "payment"}
    ]
    result = analyzer.calculate_utilization(test_data, credit_limit=1000)
    # 500 spent - 200 paid = 300 used out of 1000 = 30%
    assert result["utilization_rate"] == 0.30

def test_payment_suggestion_logic():
    """Test that suggestions trigger correctly for high utilization."""
    analyzer = CreditAnalyzer(alert_threshold=0.7)
    # 800/1000 = 80% (triggers alert)
    suggestion = analyzer.get_payment_suggestion(800, 1000)
    assert "Suggested payment" in suggestion
    
    # 100/1000 = 10% (healthy)
    suggestion = analyzer.get_payment_suggestion(100, 1000)
    assert "Utilization is healthy" in suggestion
