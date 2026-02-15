"""
src/cli.py
Command-line interface for Credit-Worthy.
"""

import click
from .database import list_accounts, init_db
from .analyzer import CreditAnalyzer

@click.group()
def cli():
    """Credit-Worthy: Local credit monitoring and optimization."""
    pass

@cli.command()
def status():
    """Print current credit status to the terminal."""
    init_db()
    accounts = list_accounts()
    if not accounts:
        click.echo("No accounts found. Add one via the web dashboard or database script.")
        return
    
    analyzer = CreditAnalyzer()
    click.echo("--- Credit Status ---")
    for acct in accounts:
        click.echo(f"{acct['name']}: ${acct['balance']} used of ${acct['credit_limit']}")
        suggestion = analyzer.get_payment_suggestion(acct['balance'], acct['credit_limit'])
        click.echo(f"  {suggestion}")
    click.echo("---------------------")

if __name__ == "__main__":
    cli()
