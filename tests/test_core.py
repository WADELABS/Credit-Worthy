import pytest
from src.analyzer import CreditAnalyzer

def test_utilization_calculation():
    """Test that utilization is calculated correctly."""
    analyzer = CreditAnalyzer()
    txns = [
        {"amount": 1000, "type": "purchase"},
        {"amount": 500, "type": "payment"}
    ]
    result = analyzer.calculate_utilization(txns, limit=5000)
    assert result["utilization_rate"] == 0.1  # (1000-500)/5000 = 0.1
    assert result["status"] == "healthy"

def test_heuristic_scoring():
    """Test that transaction scoring follows rules."""
    analyzer = CreditAnalyzer(alert_threshold=0.7)
    score = analyzer.score_transaction({"amount": 1200, "merchant": "test"})
    assert score == 0.9
    
    score = analyzer.score_transaction({"amount": 100, "merchant": "test"})
    assert score == 0.1
