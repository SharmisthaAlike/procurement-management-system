import sqlite3
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import os

db_path = 'data/procurement.db'

def forecast_material_demand(material_id, months_ahead=3):
    """
    Uses Linear Regression on historical monthly aggregation of quantity ordered
    to forecast demand for a specific material for the next `months_ahead` months.
    """
    if not os.path.exists(db_path):
        return {"error": "Database not found."}

    conn = sqlite3.connect(db_path)
    
    # Extract historical Purchase Orders for the given material
    query = f"""
    SELECT OrderDate, Quantity 
    FROM PurchaseOrders 
    WHERE MaterialID = {material_id}
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return {"error": "No historical data found for this material."}

    df['OrderDate'] = pd.to_datetime(df['OrderDate'])
    df['YearMonth'] = df['OrderDate'].dt.to_period('M')
    
    # Aggregate quantity per month
    monthly_demand = df.groupby('YearMonth')['Quantity'].sum().reset_index()
    monthly_demand['YearMonthStr'] = monthly_demand['YearMonth'].astype(str)
    
    # If we have less than 3 months of data, we cannot reliably forecast
    if len(monthly_demand) < 3:
        return {"error": "Insufficient historical data for forecasting."}
    
    # Prepare data for Simple Linear Regression
    monthly_demand['TimeIndex'] = np.arange(len(monthly_demand))
    X = monthly_demand[['TimeIndex']]
    y = monthly_demand['Quantity']

    model = LinearRegression()
    model.fit(X, y)

    # Predict future demand
    last_index = monthly_demand['TimeIndex'].iloc[-1]
    last_period = monthly_demand['YearMonth'].iloc[-1]
    
    future_indices = np.arange(last_index + 1, last_index + 1 + months_ahead).reshape(-1, 1)
    predictions = model.predict(future_indices)

    # Format the output
    forecast = []
    for i in range(months_ahead):
        next_month = last_period + (i + 1)
        forecast.append({
            "month": str(next_month),
            "predicted_demand": max(0, int(predictions[i])) # Cannot be negative
        })

    # Return combined data
    historical = monthly_demand[['YearMonthStr', 'Quantity']].rename(columns={'YearMonthStr': 'month', 'Quantity': 'actual_demand'}).to_dict(orient='records')
    
    return {
        "material_id": material_id,
        "historical": historical[-6:], # Send last 6 months 
        "forecast": forecast
    }

def get_kpis():
    """ Returns overall procurement KPIs """
    conn = sqlite3.connect(db_path)
    
    # 1. OTIF (On-Time In-Full) Rate
    otif_query = """
    SELECT 
        COUNT(*) as TotalDeliveries,
        SUM(CASE WHEN d.ActualDeliveryDate <= p.ExpectedDeliveryDate AND d.DefectQuantity = 0 THEN 1 ELSE 0 END) as OnTimeInFull
    FROM Deliveries d
    JOIN PurchaseOrders p ON d.POID = p.POID
    """
    otif_data = pd.read_sql_query(otif_query, conn).iloc[0]
    otif_rate = (otif_data['OnTimeInFull'] / otif_data['TotalDeliveries']) * 100 if otif_data['TotalDeliveries'] else 0

    # 2. Average Lead Time
    lead_query = """
    SELECT AVG(julianday(d.ActualDeliveryDate) - julianday(p.OrderDate)) as AvgLeadTime
    FROM Deliveries d
    JOIN PurchaseOrders p ON d.POID = p.POID
    """
    avg_lead_time = pd.read_sql_query(lead_query, conn).iloc[0]['AvgLeadTime']

    # 3. Overall Defect Rate
    defect_query = """
    SELECT 
        SUM(DefectQuantity) as TotalDefects,
        SUM(QuantityReceived) as TotalReceived
    FROM Deliveries
    """
    defect_data = pd.read_sql_query(defect_query, conn).iloc[0]
    defect_rate = (defect_data['TotalDefects'] / defect_data['TotalReceived']) * 100 if defect_data['TotalReceived'] else 0

    # 4. Average Cost per Order
    cost_query = "SELECT AVG(TotalCost) as AvgCost FROM PurchaseOrders"
    avg_cost = pd.read_sql_query(cost_query, conn).iloc[0]['AvgCost']

    conn.close()

    return {
        "otif_rate": round(otif_rate, 2),
        "avg_lead_time_days": round(avg_lead_time, 1) if avg_lead_time else 0,
        "defect_rate": round(defect_rate, 2),
        "avg_cost_per_order": round(avg_cost, 2) if avg_cost else 0
    }

def supplier_reliability_data():
    conn = sqlite3.connect(db_path)
    query = """
    SELECT s.Name, s.ReliabilityScore, COUNT(p.POID) as OrderCount
    FROM Suppliers s
    LEFT JOIN PurchaseOrders p ON s.SupplierID = p.SupplierID
    GROUP BY s.SupplierID
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict(orient='records')
