from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import pandas as pd
from ml_models import forecast_material_demand, get_kpis, supplier_reliability_data
import os

app = Flask(__name__)
CORS(app) # Allow Vite app to communicate with Flask

db_path = 'data/procurement.db'

@app.route('/api/kpis', methods=['GET'])
def get_kpi_route():
    try:
        kpis = get_kpis()
        return jsonify(kpis)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/forecast/<int:material_id>', methods=['GET'])
def get_forecast_route(material_id):
    try:
        forecast_data = forecast_material_demand(material_id, months_ahead=3)
        return jsonify(forecast_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/suppliers', methods=['GET'])
def get_suppliers_route():
    try:
        data = supplier_reliability_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/materials', methods=['GET'])
def get_materials_route():
    try:
        if not os.path.exists(db_path):
            return jsonify([])
        conn = sqlite3.connect(db_path)
        materials = pd.read_sql_query("SELECT MaterialID, Name, Category, CurrentStock FROM RawMaterials", conn)
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
            (data.get('Name'), data.get('Category'), int(data.get('CurrentStock') or 0), int(data.get('MinThreshold') or 0), float(data.get('CostPerUnit') or 0.0))
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
        # Enable PRAGMA foreign_keys so if there's a purchase order relying on this material, it fails securely
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("DELETE FROM RawMaterials WHERE MaterialID = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 200
    except sqlite3.IntegrityError:
        return jsonify({"error": "Cannot delete material. It is referenced by active Purchase Orders."}), 400
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

if __name__ == '__main__':
    from waitress import serve
    # Will run on port 5001 to avoid conflicts
    print("Starting server on port 5001...")
    serve(app, host="0.0.0.0", port=5001)
