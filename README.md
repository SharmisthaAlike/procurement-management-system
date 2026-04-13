# Procurement Reliability Management System

A full-stack, ML-integrated dashboard designed to tackle Problem Statement 2 (P2 - Procurement Reliability) from the SCME course guidelines. Built securely to provide Frappe-like document management scaled with high-performance metrics.

## Features

- **Analytics Dashboard**: Tracks vital KPIs live, such as OTIF Reliability, Lead Time, Defect Rate, and Cost Per Order.
- **Machine Learning Integration**: Implemented a Time-Series forecasting model using `scikit-learn` to predict future raw material demand based on historical data.
- **Frappe-like Document CMS**: Re-usable generic CRUD models to easily add or drop new Supply and Material tables internally via a beautiful glassmorphism-styled React frontend.
- **Robust Relational Data**: Data runs cleanly on an intelligently locked SQLite schema boasting strong `AUTOINCREMENT` keys, `FOREIGN_KEY` restrictions, and `DEFAULT` parameters making unexpected drops impossible!

## Technology Stack

- **Frontend**: Vite.js + React.js + Recharts (Custom Vanilla CSS components)
- **Backend / API**: Python + Flask + Pandas
- **Machine Learning**: Scikit-Learn
- **Database Engine**: SQLite 3

---

## Installation & Setup

Ensure that `npm` (Node JS) and `python3` are configured on your machine before running these steps.

### 1. Setup the Backend Environment
Open a terminal in the root folder of this project:
```bash
# Set up your python virtual environment securely
python3 -m venv backend/venv
source backend/venv/bin/activate

# Install the dependencies mapped in requirements.txt
pip install -r requirements.txt

# Generate the strictly-typed mockup database for demonstrations
python3 backend/generate_mock_data.py

# Launch the Application API (Defaults to 5001)
python3 backend/app.py
```

### 2. Setup the Frontend UI
In a separate terminal window:
```bash
# Move to the front end logic
cd frontend

# Install Vite components
npm install

# Run the live server on localhost
npm run dev
```

Navigate your browser to the local address (typically `http://localhost:5173`) to view and interact with the Procurement Reliability Dashboard!
