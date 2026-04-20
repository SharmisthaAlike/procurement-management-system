# Procurement Reliability Management System

> **Course:** SCME-23CS · Problem Statement P2 — Procurement Reliability  
> **Stack:** React + Vite · Flask · SQLite · scikit-learn · Recharts

A full-stack, ML-integrated supply chain intelligence dashboard built to combat the **P2 – Procurement Reliability** problem: *"Organisations struggle with timely and reliable procurement of raw materials, resulting in supply chain disruptions, increased costs, and delayed deliveries."*

---

## Features

### 📊 10 Real-Time KPIs
Every KPI is colour-coded with threshold logic (🟢 Good / 🟡 Warn / 🔴 Danger):

| KPI | What It Measures | Target |
|-----|-----------------|--------|
| **OTIF Rate** | % deliveries that were On-Time AND In-Full with zero defects | ≥ 85% |
| **Avg Lead Time** | Calendar days from Purchase Order → Actual Delivery | ≤ 20 days |
| **Late Delivery Rate** | % deliveries past the expected date | ≤ 15% |
| **Defect Rate** | Defective units ÷ Total units received | ≤ 5% |
| **Stockout Risk Count** | Materials where stock < minimum threshold | 0 |
| **Supplier Fill Rate** | Qty received ÷ Qty ordered | ≥ 95% |
| **Avg Delay per Order** | Avg days a delivery exceeds its promised date | ≤ 2 days |
| **Spend Concentration** | % of total spend locked in single top supplier | ≤ 30% |
| **Avg Cost per Order** | Average value of a Purchase Order | — |
| **Total Procurement Spend** | Rolling 12-month procurement value | — |

### 📈 4 Interactive Charts
- **Demand Forecast** — ML Linear Regression predicting next 3 months per material
- **On-Time vs Late Deliveries** — Area chart showing monthly delivery reliability trend
- **Spend by Supplier** — Horizontal bar chart of top 8 suppliers by procurement value
- **Supplier Risk Matrix** — Bubble scatter plot: Order Volume vs Reliability (bubble = spend)

### 🚨 Stockout Risk Alert Banner
Auto-fires at the top of the dashboard when any material stock falls below its minimum threshold, listing affected material names.

### 📋 Purchase Orders View
Full tabular view of all POs with On-Time / Late / Pending status badges, defect counts, and cost.

### 📁 CSV Import Tool
- Drag-and-drop CSV upload for any of the 4 database tables
- Live preview of the first 5 rows before committing
- Download sample CSVs with realistic data for each table
- Toast notifications on success/error

### 🛠 CRUD Management
Add and delete Raw Materials and Suppliers through modal forms with validation.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 + Vite, Recharts, Lucide Icons |
| **Styling** | Vanilla CSS (Glassmorphism + animated mesh gradients) |
| **Backend API** | Python 3, Flask, Flask-CORS, Waitress (WSGI) |
| **Data Processing** | Pandas, NumPy |
| **Machine Learning** | scikit-learn (Linear Regression) |
| **Database** | SQLite 3 |

---

## Project Structure

```
procurement-management-system/
├── backend/
│   ├── app.py                  # Flask API — all routes
│   ├── ml_models.py            # KPI computations + ML forecasting
│   ├── generate_mock_data.py   # One-time DB seeder (1000 POs)
│   └── venv/                   # Python virtual environment
├── data/
│   └── procurement.db          # SQLite database
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main app + all views
│   │   ├── index.css           # Design system (tokens, components)
│   │   └── components/
│   │       ├── KPICard.jsx     # Status-aware KPI card
│   │       ├── CSVUpload.jsx   # Drag-and-drop CSV importer
│   │       ├── DataListView.jsx # Searchable data table
│   │       └── DataFormModal.jsx # Add-record modal form
│   └── package.json
├── requirements.txt
└── README.md
```

---

## Database Schema

```
Suppliers ──────────────────────────────────────────────┐
  SupplierID  (PK, AUTOINCREMENT)                       │
  Name        TEXT NOT NULL                             │
  Category    TEXT NOT NULL                             │  FK
  ReliabilityScore  REAL DEFAULT 1.0                    │
                                                        ▼
RawMaterials                            PurchaseOrders ─────────── Deliveries
  MaterialID  (PK, AUTOINCREMENT)         POID  (PK)               DeliveryID (PK)
  Name        TEXT NOT NULL        FK ─── SupplierID               POID  (FK → PO)
  Category    TEXT NOT NULL        FK ─── MaterialID               ActualDeliveryDate
  CurrentStock  INTEGER                   OrderDate                QuantityReceived
  MinThreshold  INTEGER                   ExpectedDeliveryDate      DefectQuantity
  CostPerUnit   REAL                      Quantity
                                          TotalCost
```

---

## Installation & Setup

> **Prerequisites:** Python 3.9+, Node.js 18+

### 1 — Clone & prepare the database

```bash
git clone https://github.com/SharmisthaAlike/procurement-management-system.git
cd procurement-management-system

# Create and activate Python virtual environment
python3 -m venv backend/venv
source backend/venv/bin/activate        # Windows: backend\venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Seed the database with 1 000 realistic purchase orders
python3 backend/generate_mock_data.py
```

### 2 — Start the backend API

```bash
# From the project root (venv must be active)
cd backend && python app.py
# ✓ API running at http://localhost:5001
```

### 3 — Start the frontend

Open a **second terminal** in the project root:

```bash
cd frontend
npm install        # first time only
npm run dev
# ✓ UI running at http://localhost:5173
```

Open **http://localhost:5173** in your browser.

---

## User Guide

### Navigating the Dashboard

The **left sidebar** is divided into three sections:

| Section | Views |
|---------|-------|
| **ANALYTICS** | Dashboard, Purchase Orders |
| **MASTER DATA** | Raw Materials, Suppliers |
| **TOOLS** | Import CSV |

---

### Understanding the KPI Cards

- Cards pulse **red** if a critical threshold is breached
- Trend arrows (↑ / ↓) show whether the metric is moving in a good or bad direction
- A **red stockout banner** appears at the top of the dashboard if any material stock drops below its `MinThreshold`

---

### Importing Data via CSV

1. Click **Import CSV** in the sidebar
2. Select the **target table** from the four buttons (Purchase Orders, Deliveries, Suppliers, Raw Materials)
3. Click **Download Sample CSV** to get a pre-formatted template with realistic example rows
4. Fill in your data following the template, then drag-and-drop the file (or click to browse)
5. Inspect the **5-row preview** — if columns look correct, click **Upload**
6. A toast notification confirms how many rows were inserted

> **Required columns per table:**
>
> | Table | Required Columns |
> |-------|-----------------|
> | `PurchaseOrders` | `SupplierID, MaterialID, OrderDate, ExpectedDeliveryDate, Quantity, TotalCost` |
> | `Deliveries` | `POID, ActualDeliveryDate, QuantityReceived, DefectQuantity` |
> | `Suppliers` | `Name, Category, ReliabilityScore` |
> | `RawMaterials` | `Name, Category, CurrentStock, MinThreshold, CostPerUnit` |

---

### Adding Records Manually

- Go to **Raw Materials** or **Suppliers** and click **+ Add New**
- Fill the form and click **Save Record**
- Records with `CurrentStock < MinThreshold` will be highlighted in red in the table and contribute to the stockout risk count

---

## API Reference

Base URL: `http://localhost:5001/api`

### KPIs & Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/kpis` | Returns all 10 KPIs + chart data (`delivery_trend`, `spend_by_supplier`) |
| `GET` | `/api/forecast/<material_id>` | Returns historical demand + 3-month ML forecast for a material |

**Example — `/api/kpis` response (excerpt):**
```json
{
  "otif_rate": 78.4,
  "avg_lead_time_days": 17.8,
  "late_delivery_rate": 33.6,
  "defect_rate": 4.45,
  "stockout_risk_count": 2,
  "risk_materials": "Material 2, Material 9",
  "fill_rate": 100.0,
  "avg_delay_days": 1.1,
  "spend_concentration_pct": 11.6,
  "top_supplier_name": "Supplier C",
  "total_spend": 28410174.3,
  "delivery_trend": [ { "Month": "2025-04", "OnTime": 31, "Late": 22 }, "..." ],
  "spend_by_supplier": [ { "Name": "Supplier C", "TotalSpend": 3304007 }, "..." ]
}
```

### Suppliers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/suppliers` | List all suppliers with order count and total spend |
| `POST` | `/api/suppliers` | Add a new supplier |
| `DELETE` | `/api/suppliers/<id>` | Delete a supplier (blocked if active POs exist) |

**POST body:**
```json
{ "Name": "Tata Steel Ltd", "Category": "Metals", "ReliabilityScore": 0.96 }
```

### Raw Materials

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/materials` | List all materials with stock levels |
| `POST` | `/api/materials` | Add a new material |
| `DELETE` | `/api/materials/<id>` | Delete a material (blocked if referenced by POs) |

**POST body:**
```json
{ "Name": "Cold Rolled Steel Coil", "Category": "Metals", "CurrentStock": 850, "MinThreshold": 300, "CostPerUnit": 295.00 }
```

### Purchase Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/purchase-orders` | List last 200 POs with supplier name, material name, status |

### CSV Import

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload-csv` | Upload a CSV file (`multipart/form-data`: `file` + `table` field) |
| `GET` | `/api/sample-csv/<table_name>` | Download a sample CSV for `PurchaseOrders`, `Deliveries`, `Suppliers`, or `RawMaterials` |

**Sample CSV download URLs:**
```
GET http://localhost:5001/api/sample-csv/PurchaseOrders
GET http://localhost:5001/api/sample-csv/Deliveries
GET http://localhost:5001/api/sample-csv/Suppliers
GET http://localhost:5001/api/sample-csv/RawMaterials
```

**Upload with curl:**
```bash
curl -X POST http://localhost:5001/api/upload-csv \
  -F "table=Suppliers" \
  -F "file=@my_suppliers.csv"
```

---

## Sample Data Reference

Sample CSVs use realistic Indian manufacturing supply chain data. Download them from the UI (**Import CSV → Download Sample CSV**) or directly via the API above.

### Suppliers sample
| Name | Category | ReliabilityScore |
|------|----------|-----------------|
| Tata Steel Ltd | Metals | 0.96 |
| JSW Steel Pvt Ltd | Metals | 0.93 |
| BASF India Ltd | Chemicals | 0.91 |
| Deepak Nitrite Ltd | Chemicals | 0.87 |
| Molex India Pvt Ltd | Electronics | 0.95 |
| TE Connectivity India | Electronics | 0.89 |
| Supreme Industries | Plastics | 0.83 |
| Nilkamal Ltd | Plastics | 0.79 |

### Raw Materials sample
| Name | Category | CostPerUnit |
|------|----------|------------|
| Cold Rolled Steel Coil (0.8mm) | Metals | ₹295/coil |
| Hot Dip Galvanised Sheet | Metals | ₹218/sheet |
| Sulphuric Acid (Technical Grade) | Chemicals | ₹320/drum |
| Isocyanate MDI 44V20 | Chemicals | ₹345/kg |
| Benzene Purified (99.9%) | Chemicals | ₹170/litre |
| SMD Resistor 0402 10K | Electronics | ₹0.052/unit |
| Molex MicroFit 3.0 Connector 8P | Electronics | ₹23.90/unit |
| Nylon 6/6 Natural Granules | Plastics | ₹27/kg |
| Polypropylene Copolymer (MFI 12) | Plastics | ₹19.50/kg |
| HDPE Pipe Grade Resin | Plastics | ₹31/kg |

> **Tip:** Two items (Benzene and HDPE Resin) are intentionally seeded at stockout risk levels so you can immediately see the alert banner in action.

---

## Re-seeding the Database

If you want to reset to fresh mock data:

```bash
# From project root, with venv active
python3 backend/generate_mock_data.py
```

This drops and recreates all four tables with **1 000 randomised Purchase Orders** spanning the past 12 months, 10 suppliers, and 15 materials.

---

## License

MIT
