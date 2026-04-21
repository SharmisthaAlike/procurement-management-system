from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import pandas as pd
from ml_models import (
    forecast_material_demand, get_kpis, supplier_reliability_data,
    calculate_supplier_reliability_scores, predict_delay_probability,
    get_procurement_alerts, get_purchase_orders
)
import os
import io

# Resolve DB path relative to this file (backend/../data/procurement.db)
_HERE = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(_HERE, '..', 'data', 'procurement.db')

app = Flask(__name__)
CORS(app)

# db_path defined above using __file__

# ── KPI ──────────────────────────────────────────────────────────────────────
@app.route('/api/kpis', methods=['GET'])
def get_kpi_route():
    try:
        return jsonify(get_kpis())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── FORECAST ─────────────────────────────────────────────────────────────────
@app.route('/api/forecast/<int:material_id>', methods=['GET'])
def get_forecast_route(material_id):
    try:
        return jsonify(forecast_material_demand(material_id, months_ahead=3))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── SUPPLIERS ─────────────────────────────────────────────────────────────────
@app.route('/api/suppliers', methods=['GET'])
def get_suppliers_route():
    try:
        return jsonify(supplier_reliability_data())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/suppliers', methods=['POST'])
def add_supplier_route():
    try:
        data = request.json
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Suppliers (Name, Category, ReliabilityScore) VALUES (?, ?, ?)",
            (data.get('Name'), data.get('Category'), float(data.get('ReliabilityScore') or 1.0))
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/suppliers/<int:id>', methods=['DELETE'])
def delete_supplier_route(id):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("DELETE FROM Suppliers WHERE SupplierID = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 200
    except sqlite3.IntegrityError:
        return jsonify({"error": "Cannot delete supplier. They have active Purchase Orders."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/suppliers/ranking', methods=['GET'])
def get_supplier_ranking():
    """
    Returns suppliers ranked by reliability score (highest to lowest).
    Each supplier includes:
    - reliability_score (0-100)
    - otif (on-time in-full %)
    - avg_lead_time_days
    - defect_rate (%)
    - cost_efficiency
    """
    try:
        suppliers = calculate_supplier_reliability_scores()
        return jsonify(suppliers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/predict/delay/<int:supplier_id>', methods=['GET'])
def predict_delay_route(supplier_id):
    """
    Predicts delay probability for a supplier.
    Optional query param: ?material_id=<id>
    
    Returns: {
        "supplier_id": int,
        "material_id": int or null,
        "delay_probability": float (0-100),
        "risk_level": "LOW" | "MEDIUM" | "HIGH",
        "reasoning": str
    }
    """
    try:
        material_id = request.args.get('material_id', type=int)
        prediction = predict_delay_probability(supplier_id, material_id)
        return jsonify(prediction)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts_route():
    """
    Returns active procurement risk alerts.
    
    Alert types:
    - LOW_RELIABILITY: Supplier score < 60
    - HIGH_DELAY_RISK: Predicted delay probability > threshold
    - LOW_STOCK: Material below minimum threshold
    """
    try:
        alerts = get_procurement_alerts()
        return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── MATERIALS ─────────────────────────────────────────────────────────────────
@app.route('/api/materials', methods=['GET'])
def get_materials_route():
    try:
        if not os.path.exists(db_path):
            return jsonify([])
        conn = sqlite3.connect(db_path)
        materials = pd.read_sql_query(
            "SELECT MaterialID, Name, Category, CurrentStock, MinThreshold, CostPerUnit FROM RawMaterials ORDER BY Name",
            conn
        )
        conn.close()
        materials = materials.replace({float('nan'): None})
        return jsonify(materials.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/materials', methods=['POST'])
def add_material_route():
    try:
        data = request.json
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO RawMaterials (Name, Category, CurrentStock, MinThreshold, CostPerUnit) VALUES (?, ?, ?, ?, ?)",
            (data.get('Name'), data.get('Category'),
             int(data.get('CurrentStock') or 0),
             int(data.get('MinThreshold') or 0),
             float(data.get('CostPerUnit') or 0.0))
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/materials/<int:id>', methods=['DELETE'])
def delete_material_route(id):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("DELETE FROM RawMaterials WHERE MaterialID = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 200
    except sqlite3.IntegrityError:
        return jsonify({"error": "Cannot delete material. It is referenced by active Purchase Orders."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── PURCHASE ORDERS ───────────────────────────────────────────────────────────
@app.route('/api/purchase-orders', methods=['GET'])
def get_purchase_orders_route():
    try:
        return jsonify(get_purchase_orders())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── CSV UPLOAD ────────────────────────────────────────────────────────────────
ALLOWED_TABLES = {
    'PurchaseOrders':  ['SupplierID', 'MaterialID', 'OrderDate', 'ExpectedDeliveryDate', 'Quantity', 'TotalCost'],
    'Deliveries':      ['POID', 'ActualDeliveryDate', 'QuantityReceived', 'DefectQuantity'],
    'Suppliers':       ['Name', 'Category', 'ReliabilityScore'],
    'RawMaterials':    ['Name', 'Category', 'CurrentStock', 'MinThreshold', 'CostPerUnit'],
}

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv_route():
    try:
        table_name = request.form.get('table')
        if table_name not in ALLOWED_TABLES:
            return jsonify({"error": f"Invalid table. Choose from: {', '.join(ALLOWED_TABLES.keys())}"}), 400

        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded."}), 400

        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "Only CSV files are supported."}), 400

        df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))

        required_cols = ALLOWED_TABLES[table_name]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return jsonify({"error": f"Missing required columns: {', '.join(missing)}"}), 400

        # Keep only the required columns to avoid injection of unknown columns
        df = df[required_cols]

        conn = sqlite3.connect(db_path)
        rows_inserted = len(df)
        df.to_sql(table_name, conn, if_exists='append', index=False)
        conn.commit()
        conn.close()

        return jsonify({"success": True, "rows_inserted": rows_inserted, "table": table_name}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── SAMPLE CSV DOWNLOAD ───────────────────────────────────────────────────────
@app.route('/api/sample-csv/<table_name>', methods=['GET'])
def download_sample_csv(table_name):
    """Return a pre-built sample CSV for the requested table."""
    import csv, io as _io
    from flask import Response

    samples = {
        'PurchaseOrders': [
            ['SupplierID','MaterialID','OrderDate','ExpectedDeliveryDate','Quantity','TotalCost'],
            # Steel & Metals POs
            [1, 1, '2025-02-03', '2025-02-18', 500, 147500.00],
            [1, 2, '2025-02-10', '2025-02-25', 200,  43600.00],
            [2, 3, '2025-02-12', '2025-03-01', 120,  38400.00],
            # Chemical supply POs
            [3, 4, '2025-02-14', '2025-02-28',  80,  26400.00],
            [3, 5, '2025-03-01', '2025-03-15', 300,  51000.00],
            # Electronics POs
            [4, 6, '2025-03-03', '2025-03-20', 600,  31200.00],
            [4, 7, '2025-03-05', '2025-03-22', 250,  59750.00],
            # Plastics POs
            [5, 8, '2025-03-08', '2025-03-25', 900,  24300.00],
            [5, 9, '2025-03-10', '2025-03-28', 150,  36750.00],
            # Mixed cross-material POs
            [6, 1, '2025-03-12', '2025-03-30', 400, 118000.00],
            [7, 3, '2025-03-15', '2025-04-02', 100,  32000.00],
            [8, 5, '2025-03-18', '2025-04-05', 220,  37400.00],
        ],
        'Deliveries': [
            ['POID','ActualDeliveryDate','QuantityReceived','DefectQuantity'],
            # On-time deliveries
            [1, '2025-02-17', 500,  4],
            [2, '2025-02-24', 200,  0],
            [3, '2025-02-28', 120,  3],
            # Slightly delayed
            [4, '2025-03-02',  80,  1],
            [5, '2025-03-17', 295, 12],
            # Electronics on-time
            [6, '2025-03-20', 600,  8],
            [7, '2025-03-23', 250,  2],
            # Plastics — significant delay and defects
            [8, '2025-04-01', 875, 28],
            [9, '2025-03-29', 150,  5],
            # Late with defects
            [10, '2025-04-05', 390, 18],
            [11, '2025-04-08',  98,  0],
            [12, '2025-04-09', 218,  7],
        ],
        'Suppliers': [
            ['Name','Category','ReliabilityScore'],
            ['Tata Steel Ltd',           'Metals',       0.96],
            ['JSW Steel Pvt Ltd',         'Metals',       0.93],
            ['BASF India Ltd',            'Chemicals',    0.91],
            ['Deepak Nitrite Ltd',        'Chemicals',    0.87],
            ['Molex India Pvt Ltd',       'Electronics',  0.95],
            ['TE Connectivity India',     'Electronics',  0.89],
            ['Supreme Industries',        'Plastics',     0.83],
            ['Nilkamal Ltd',              'Plastics',     0.79],
        ],
        'RawMaterials': [
            ['Name','Category','CurrentStock','MinThreshold','CostPerUnit'],
            ['Cold Rolled Steel Coil (0.8mm)',   'Metals',      850,  300,  295.00],
            ['Hot Dip Galvanised Sheet',          'Metals',      420,  150,  218.00],
            ['Sulphuric Acid (Technical Grade)',  'Chemicals',   210,   80,  320.00],
            ['Isocyanate MDI 44V20',              'Chemicals',   155,   60,  345.00],
            ['Benzene Purified (99.9%)',           'Chemicals',    45,   75,  170.00],  # ← at stockout risk
            ['SMD Resistor 0402 10K',             'Electronics', 52000, 20000,  0.052],
            ['Molex MicroFit 3.0 Connector 8P',  'Electronics',  1200,  500,  23.90],
            ['Nylon 6/6 Natural Granules',        'Plastics',    1800,  600,  27.00],
            ['Polypropylene Copolymer (MFI 12)',  'Plastics',    2400,  800,  19.50],
            ['HDPE Pipe Grade Resin',             'Plastics',     320,  400,  31.00],  # ← at stockout risk
        ],
    }

    if table_name not in samples:
        return jsonify({"error": "Unknown table"}), 404

    output = _io.StringIO()
    writer = csv.writer(output)
    writer.writerows(samples[table_name])
    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment; filename=sample_{table_name}.csv"}
    )

>>>>>>> 0da7d23e0eeb64b9f22b620a8a8fdb71f866faa6

if __name__ == '__main__':
    from waitress import serve
    print("Starting Procurement API on port 5001...")
    serve(app, host="0.0.0.0", port=5001)
