# CredStack

A local tool for monitoring credit utilization. CredStack helps you:
- Track credit usage across multiple accounts.
- Use rule-based logic to plan payments.
- Schedule automated reminders for account checks.

## Purpose

CredStack is designed to run locally, keeping financial data on your machine rather than in the cloud.

## Installation

```bash
git clone https://github.com/WADELABS/credstack.git
cd credstack
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000` to view the tool.

## Technical Details

CredStack uses configurable logic for:
- **Usage Monitoring**: Tracks balance relative to limits.
- **Alert Thresholds**: Configurable triggers for utilization spikes.
- **Payment Prioritization**: Identifies accounts that need attention based on interest or balance.

Configuration is handled in `config.yaml`:
```yaml
logic:
  alert_threshold: 0.8
  min_payment_alert: true
```

## Stack
- Python/Flask
- SQLite
- HTML/CSS/JS

## Testing
```bash
pytest tests/
```

## License
MIT
