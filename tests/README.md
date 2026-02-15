# CredStack Testing Guide 🧪

CredStack includes a suite of tests to ensure the core logic and web application are functional.

## Test Structure

- **`tests/test_automation.py`**: Unit tests for the credit automation engine.
  - Verifies next-date calculations.
  - Verifies rollover logic (handling days that have already passed in the current month).
  - Verifies edge cases (like the 31st of the month).

- **`tests/test_app.py`**: Integration tests for the Flask application.
  - Verifies the landing page loads successfully.
  - Verifies the login flow and session creation.
  - Verifies account addition and database integration.

## How to Run the Tests

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Execute Test Runner**
   ```bash
   python -m unittest discover tests
   ```

## Test Philosophy
The tests use a combination of standard `unittest` and Flask's built-in test client. Integration tests use a temporary SQLite database (`tempfile`) to ensure a clean state and avoid polluting your production data.
