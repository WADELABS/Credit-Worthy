"""
cli.py
Command-line interface for CredStack local optimization.
"""

import click
from src.analyzer import CreditAnalyzer

@click.group()
def cli():
    """CredStack: Local credit monitoring and optimization."""
    pass

@cli.command()
@click.option('--limit', type=float, required=True, help="Total credit limit.")
def status(limit):
    """View current utilization status."""
    analyzer = CreditAnalyzer()
    # In a real app, this would fetch data from a local database
    # For the demo, we use a sample transaction set
    transactions = [
        {"amount": 1000, "type": "purchase"},
        {"amount": 500, "type": "payment"}
    ]
    result = analyzer.calculate_utilization(transactions, limit)
    
    click.echo(f"Balance: ${result['balance']}")
    click.echo(f"Utilization: {result['utilization_rate']*100}%")
    click.echo(f"Status: {result['status'].upper()}")

@cli.command()
def score():
    """Score individual transactions for priority."""
    analyzer = CreditAnalyzer()
    sample_tx = {"amount": 1200, "merchant": "Automated Check"}
    score = analyzer.score_transaction(sample_tx)
    click.echo(f"Transaction Score: {score} (Priority: {'HIGH' if score > 0.7 else 'NORMAL'})")

if __name__ == '__main__':
    cli()
