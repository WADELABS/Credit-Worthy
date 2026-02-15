"""
src/app.py
Web interface for the Credit-Worthy dashboard.
"""

from flask import Flask, render_template, request, redirect, url_for
from .database import list_accounts, add_transaction, add_account, init_db
from .analyzer import CreditAnalyzer

app = Flask(__name__, template_folder='../templates')
analyzer = CreditAnalyzer()

@app.route("/")
def index():
    """Main dashboard view."""
    accounts = list_accounts()
    # Calculate stats for each account
    for acct in accounts:
        # Transactions should be fetched per account, simplified for demo
        acct['utilization'] = round((acct['balance'] / acct['credit_limit'] * 100), 1) if acct['credit_limit'] > 0 else 0
        acct['suggestion'] = analyzer.get_payment_suggestion(acct['balance'], acct['credit_limit'])
    
    return render_template("index.html", accounts=accounts)

@app.route("/add_account", methods=["POST"])
def new_account():
    """Creates a new credit account."""
    name = request.form.get("name")
    limit = float(request.form.get("limit"))
    add_account(name, limit)
    return redirect(url_for("index"))

@app.route("/add_transaction", methods=["POST"])
def new_transaction():
    """Adds a transaction to an account."""
    acct_id = int(request.form.get("account_id"))
    amount = float(request.form.get("amount"))
    tx_type = request.form.get("type")
    add_transaction(acct_id, amount, tx_type)
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
