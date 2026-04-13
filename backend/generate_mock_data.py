import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Create data directory
os.makedirs('data', exist_ok=True)
db_path = 'data/procurement.db'

def create_schema(cursor):
    cursor.execute("DROP TABLE IF EXISTS Deliveries")
    cursor.execute("DROP TABLE IF EXISTS PurchaseOrders")
    cursor.execute("DROP TABLE IF EXISTS RawMaterials")
    cursor.execute("DROP TABLE IF EXISTS Suppliers")

    cursor.execute("""
    CREATE TABLE Suppliers (
        SupplierID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Category TEXT NOT NULL,
        ReliabilityScore REAL DEFAULT 1.0
    )
    """)
    
    cursor.execute("""
    CREATE TABLE RawMaterials (
        MaterialID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Category TEXT NOT NULL,
        CurrentStock INTEGER DEFAULT 0,
        MinThreshold INTEGER DEFAULT 0,
        CostPerUnit REAL DEFAULT 0.0
    )
    """)
    
    cursor.execute("""
    CREATE TABLE PurchaseOrders (
        POID INTEGER PRIMARY KEY AUTOINCREMENT,
        SupplierID INTEGER NOT NULL,
        MaterialID INTEGER NOT NULL,
        OrderDate DATE NOT NULL,
        ExpectedDeliveryDate DATE NOT NULL,
        Quantity INTEGER DEFAULT 1,
        TotalCost REAL DEFAULT 0.0,
        FOREIGN KEY(SupplierID) REFERENCES Suppliers(SupplierID) ON DELETE RESTRICT,
        FOREIGN KEY(MaterialID) REFERENCES RawMaterials(MaterialID) ON DELETE RESTRICT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE Deliveries (
        DeliveryID INTEGER PRIMARY KEY AUTOINCREMENT,
        POID INTEGER NOT NULL,
        ActualDeliveryDate DATE,
        QuantityReceived INTEGER DEFAULT 0,
        DefectQuantity INTEGER DEFAULT 0,
        FOREIGN KEY(POID) REFERENCES PurchaseOrders(POID) ON DELETE CASCADE
    )
    """)

def generate_data(conn):
    suppliers = pd.DataFrame({
        'SupplierID': range(1, 11),
        'Name': [f'Supplier {chr(65+i)}' for i in range(10)],
        'Category': np.random.choice(['Electronics', 'Metals', 'Plastics', 'Chemicals'], 10),
        'ReliabilityScore': np.random.uniform(0.7, 0.99, 10).round(2)
    })
    
    materials = pd.DataFrame({
        'MaterialID': range(1, 16),
        'Name': [f'Material {i}' for i in range(1, 16)],
        'Category': np.random.choice(['Electronics', 'Metals', 'Plastics', 'Chemicals'], 15),
        'CurrentStock': np.random.randint(50, 500, 15),
        'MinThreshold': np.random.randint(20, 100, 15),
        'CostPerUnit': np.random.uniform(10.0, 500.0, 15).round(2)
    })
    
    start_date = datetime.now() - timedelta(days=365)
    po_list = []
    delivery_list = []
    
    for i in range(1, 1001):
        supplier_id = np.random.choice(suppliers['SupplierID'])
        material_id = np.random.choice(materials['MaterialID'])
        order_date = start_date + timedelta(days=np.random.randint(0, 350))
        expected_delivery = order_date + timedelta(days=np.random.randint(5, 30))
        qty = np.random.randint(10, 200)
        cost_per_unit = float(materials.loc[materials['MaterialID'] == material_id, 'CostPerUnit'].values[0])
        total_cost = qty * cost_per_unit
        
        po_list.append((i, supplier_id, material_id, order_date.strftime('%Y-%m-%d'), expected_delivery.strftime('%Y-%m-%d'), qty, round(total_cost, 2)))
        
        # Reliability determines delivery delay and defect quantity
        reliability = float(suppliers.loc[suppliers['SupplierID'] == supplier_id, 'ReliabilityScore'].values[0])
        delay_days = int(np.random.normal(0, (1.0 - reliability) * 20))
        actual_delivery = expected_delivery + timedelta(days=max(0, delay_days))
        
        defect_rate = max(0, np.random.normal(0.05, (1.0 - reliability) * 0.1))
        defect_qty = int(qty * defect_rate)
        
        delivery_list.append((i, i, actual_delivery.strftime('%Y-%m-%d'), qty, defect_qty))

    po_df = pd.DataFrame(po_list, columns=['POID', 'SupplierID', 'MaterialID', 'OrderDate', 'ExpectedDeliveryDate', 'Quantity', 'TotalCost'])
    del_df = pd.DataFrame(delivery_list, columns=['DeliveryID', 'POID', 'ActualDeliveryDate', 'QuantityReceived', 'DefectQuantity'])

    suppliers.to_sql('Suppliers', conn, if_exists='append', index=False)
    materials.to_sql('RawMaterials', conn, if_exists='append', index=False)
    po_df.to_sql('PurchaseOrders', conn, if_exists='append', index=False)
    del_df.to_sql('Deliveries', conn, if_exists='append', index=False)

if __name__ == '__main__':
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    create_schema(cursor)
    generate_data(conn)
    conn.commit()
    conn.close()
    print("Mock data generated successfully in data/procurement.db")
