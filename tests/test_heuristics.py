import pytest
from src.heuristics import UtilizationHeuristic

def test_heuristic_initialization():
    """Test that heuristic loads with default values."""
    heuristic = UtilizationHeuristic()
    assert heuristic.aggression_threshold == 0.7
    
def test_heuristic_evaluates_transaction():
    """Test that heuristic can score a sample transaction."""
    heuristic = UtilizationHeuristic()
    sample_tx = {"amount": 1001, "type": "purchase", "merchant": "test"}
    score = heuristic.evaluate(sample_tx)
    assert score == 0.9
