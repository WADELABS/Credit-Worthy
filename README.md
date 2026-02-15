# CredStack (Credit-Worthy)

[![CI](https://github.com/WADELABS/credstack/actions/workflows/ci.yml/badge.svg)](https://github.com/WADELABS/credstack/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A privacy-first credit utilization optimizer that runs locally. CredStack helps you:
- Track credit usage across accounts
- Apply custom heuristics to optimize payments
- Schedule automated recommendations

## Why CredStack?

Most credit tools upload your data to the cloud. CredStack keeps everything on your machine. Your financial data never leaves your control.

## Quick Start

```bash
# Clone and run
git clone https://github.com/WADELABS/credstack.git
cd credstack
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:5000`

## How It Works

CredStack uses three configurable heuristics:
- **Proactive Signal**: Detects upcoming utilization spikes
- **Aggression Threshold**: Controls how aggressively to optimize
- **Liability Neutralization**: Identifies high-interest targets

Configure them in `config.yaml`:
```yaml
heuristics:
  proactive_signal: 0.8
  aggression_threshold: 0.6
  liability_neutralization: true
```

## Tech Stack
- Python/Flask backend
- SQLite for local storage
- HTML/CSS/JS frontend (vanilla)
- Built-in scheduler for automated checks

## Tests
```bash
pytest tests/ --cov=src
```

## License
MIT
