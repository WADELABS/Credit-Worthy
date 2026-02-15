# CredStack: Automation Substrate (Phase 2) 🛡️

> **"Stop guessing, start automating."**

CredStack is a precision engineering tool designed for the automated neutralization of interest-bearing liabilities. Moving beyond simple tracking, Phase 2 establishes a high-fidelity automation substrate that ensures maximum credit salience and data sovereignty through local-first architecture.

## 🏛️ Architectural Ethos: Automation Substrate

Unlike traditional financial trackers, CredStack operates as an active substrate. It employs heuristic logic to manage credit utilization before it impacts your financial profile.

### 🧠 Utilization Management Heuristics
CredStack doesn't just remind you of due dates. It implements **Utilization Neutralization**:
- **Proactive Signal**: Alerts are triggered `X` days before the **Statement Close Date**, not the due date.
- **Aggression Thresholds**: Configurable targets (e.g., <10% utilization) drive the automation engine's urgency.
- **Liability Neutralization**: Automated workflows target the reduction of reported balances to maintain optimal credit scoring salience.

## 🛡️ Privacy Architecture & Data Sovereignty

Financial data is a primary vector for privacy erosion. CredStack solves this through **Absolute Sovereignty**:
- **Local-Only Substrate**: Your data lives in a local SQLite database at `database/credstack.db`.
- **Zero-Cloud Footprint**: No external APIs, no cloud sync, and no third-party telemetry.
- **Hermetic Execution**: All calculations and schedules run locally on your hardware.

## ⚙️ Engineering Configuration (`config.yaml`)

Fine-tune the aggression of your automation substrate:

```yaml
automation:
  utilization:
    target_maximum: 10.0      # Maximum salience threshold
    warning_threshold: 30.0   # Liability breach alert
    neutralization_lead_time_days: 3 # Proactive lead time
```

## 🚀 Quick Start

1. **Initialize Substrate**
   ```bash
   pip install -r requirements.txt
   python setup.py
   ```

2. **Launch Dashboard**
   ```bash
   python app.py
   ```

3. **Deploy Scheduler**
   ```bash
   python workers/scheduler.py
   ```

## 🛠️ Technology Stack
- **Core Engine**: Python 3.11+ / Flask
- **Persistence**: SQLite (Local-First)
- **Styling**: Wadelabs Glassmorphism Interface
- **Automation**: Custom Heuristic Scheduler

---
*Part of the WADELABS Precision Engineering Suite.*