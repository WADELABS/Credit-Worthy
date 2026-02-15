"""
app.py
Main Flask application for CredStack Dashboard.
"""

from flask import Flask, render_to_string
import os

app = Flask(__name__)

@app.route('/')
def dashboard():
    """
    Renders the local-first credit optimization dashboard.
    """
    return "<h1>CredStack Dashboard (Local-First Portfolio Ready)</h1><p>Heuristics: Active</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
