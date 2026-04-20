import sqlite3
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import os

# Always resolve relative to this file regardless of CWD
_HERE = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(_HERE, '..', 'data', 'procurement.db')

def forecast_material_demand(material_id, months_ahead=3):
    """
    Uses Linear Regression on historical monthly aggregation of quantity ordered
    to forecast demand for a specific material for the next `months_ahead` months.
    """
    if not os.path.exists(db_path):
        return {"error": "Database not found."}

    conn = sqlite3.connect(db_path)
    
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
    
    monthly_demand = df.groupby('YearMonth')['Quantity'].sum().reset_index()
    monthly_demand['YearMonthStr'] = monthly_demand['YearMonth'].astype(str)
    
    if len(monthly_demand) < 3:
        return {"error": "Insufficient historical data for forecasting."}
    
    monthly_demand['TimeIndex'] = np.arange(len(monthly_demand))
    X = monthly_demand[['TimeIndex']]
    y = monthly_demand['Quantity']

    model = LinearRegression()
    model.fit(X, y)

    last_index = monthly_demand['TimeIndex'].iloc[-1]
    last_period = monthly_demand['YearMonth'].iloc[-1]
    
    future_indices = np.arange(last_index + 1, last_index + 1 + months_ahead).reshape(-1, 1)
    predictions = model.predict(future_indices)

    forecast = []
    for i in range(months_ahead):
        next_month = last_period + (i + 1)
        forecast.append({
            "month": str(next_month),
            "predicted_demand": max(0, int(predictions[i]))
        })

    historical = monthly_demand[['YearMonthStr', 'Quantity']].rename(
        columns={'YearMonthStr': 'month', 'Quantity': 'actual_demand'}
    ).to_dict(orient='records')
    
    return {
        "material_id": material_id,
        "historical": historical[-6:],
        "forecast": forecast
    }


def get_kpis():
    """Returns comprehensive procurement reliability KPIs."""
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
    total_deliveries = otif_data['TotalDeliveries'] or 1
    otif_rate = (otif_data['OnTimeInFull'] / total_deliveries) * 100

    # 2. Average Lead Time (Order Date → Actual Delivery)
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
    cost_query = "SELECT AVG(TotalCost) as AvgCost, SUM(TotalCost) as TotalSpend FROM PurchaseOrders"
    cost_data = pd.read_sql_query(cost_query, conn).iloc[0]
    avg_cost = cost_data['AvgCost'] or 0
    total_spend = cost_data['TotalSpend'] or 0

    # 5. Supplier Fill Rate: QuantityReceived / Quantity ordered
    fill_query = """
    SELECT 
        SUM(d.QuantityReceived) as TotalReceived,
        SUM(p.Quantity) as TotalOrdered
    FROM Deliveries d
    JOIN PurchaseOrders p ON d.POID = p.POID
    """
    fill_data = pd.read_sql_query(fill_query, conn).iloc[0]
    fill_rate = (fill_data['TotalReceived'] / fill_data['TotalOrdered']) * 100 if fill_data['TotalOrdered'] else 0

    # 6. Procurement Cycle Time (Expected vs Actual days delta = avg delay)
    cycle_query = """
    SELECT AVG(
        CASE 
            WHEN julianday(d.ActualDeliveryDate) - julianday(p.ExpectedDeliveryDate) > 0
            THEN julianday(d.ActualDeliveryDate) - julianday(p.ExpectedDeliveryDate)
            ELSE 0
        END
    ) as AvgDelay
    FROM Deliveries d
    JOIN PurchaseOrders p ON d.POID = p.POID
    """
    avg_delay = pd.read_sql_query(cycle_query, conn).iloc[0]['AvgDelay'] or 0

    # 7. Stockout Risk — materials where CurrentStock < MinThreshold
    stockout_query = """
    SELECT COUNT(*) as StockoutCount, 
           GROUP_CONCAT(Name, ', ') as RiskMaterials
    FROM RawMaterials 
    WHERE CurrentStock < MinThreshold AND MinThreshold > 0
    """
    stockout_data = pd.read_sql_query(stockout_query, conn).iloc[0]
    stockout_count = int(stockout_data['StockoutCount'] or 0)
    risk_materials = stockout_data['RiskMaterials'] or ''

    # 8. Spend Concentration — % of total spend from the top single supplier
    concentration_query = """
    SELECT s.Name, SUM(p.TotalCost) as SupplierSpend
    FROM PurchaseOrders p
    JOIN Suppliers s ON p.SupplierID = s.SupplierID
    GROUP BY p.SupplierID
    ORDER BY SupplierSpend DESC
    LIMIT 1
    """
    concentration_data = pd.read_sql_query(concentration_query, conn)
    if not concentration_data.empty and total_spend > 0:
        top_supplier_spend = concentration_data.iloc[0]['SupplierSpend']
        top_supplier_name = concentration_data.iloc[0]['Name']
        spend_concentration = (top_supplier_spend / total_spend) * 100
    else:
        spend_concentration = 0
        top_supplier_name = 'N/A'

    # 9. Late Delivery Rate
    late_query = """
    SELECT 
        COUNT(*) as Total,
        SUM(CASE WHEN julianday(d.ActualDeliveryDate) > julianday(p.ExpectedDeliveryDate) THEN 1 ELSE 0 END) as LateCount
    FROM Deliveries d
    JOIN PurchaseOrders p ON d.POID = p.POID
    """
    late_data = pd.read_sql_query(late_query, conn).iloc[0]
    late_rate = (late_data['LateCount'] / late_data['Total']) * 100 if late_data['Total'] else 0

    # 10. Monthly delivery trend (late vs on-time) for chart
    trend_query = """
    SELECT 
        strftime('%Y-%m', p.OrderDate) as Month,
        COUNT(*) as Total,
        SUM(CASE WHEN julianday(d.ActualDeliveryDate) <= julianday(p.ExpectedDeliveryDate) THEN 1 ELSE 0 END) as OnTime,
        SUM(CASE WHEN julianday(d.ActualDeliveryDate) > julianday(p.ExpectedDeliveryDate) THEN 1 ELSE 0 END) as Late
    FROM Deliveries d
    JOIN PurchaseOrders p ON d.POID = p.POID
    GROUP BY Month
    ORDER BY Month DESC
    LIMIT 12
    """
    trend_df = pd.read_sql_query(trend_query, conn)
    delivery_trend = trend_df.iloc[::-1].to_dict(orient='records')

    # 11. Spend by supplier (top 8)
    spend_by_supplier_query = """
    SELECT s.Name, SUM(p.TotalCost) as TotalSpend
    FROM PurchaseOrders p
    JOIN Suppliers s ON p.SupplierID = s.SupplierID
    GROUP BY p.SupplierID
    ORDER BY TotalSpend DESC
    LIMIT 8
    """
    spend_df = pd.read_sql_query(spend_by_supplier_query, conn)
    spend_by_supplier = spend_df.to_dict(orient='records')

    conn.close()

    return {
        # Core reliability KPIs
        "otif_rate": round(otif_rate, 1),
        "avg_lead_time_days": round(avg_lead_time, 1) if avg_lead_time else 0,
        "defect_rate": round(defect_rate, 2),
        "avg_cost_per_order": round(avg_cost, 2),
        # New KPIs
        "fill_rate": round(fill_rate, 1),
        "avg_delay_days": round(avg_delay, 1),
        "stockout_risk_count": stockout_count,
        "risk_materials": risk_materials,
        "spend_concentration_pct": round(spend_concentration, 1),
        "top_supplier_name": top_supplier_name,
        "late_delivery_rate": round(late_rate, 1),
        "total_spend": round(total_spend, 2),
        # Chart data embedded in KPIs response
        "delivery_trend": delivery_trend,
        "spend_by_supplier": spend_by_supplier,
    }


def supplier_reliability_data():
    conn = sqlite3.connect(db_path)
    query = """
    SELECT s.SupplierID, s.Name, s.ReliabilityScore, s.Category, COUNT(p.POID) as OrderCount,
           COALESCE(SUM(p.TotalCost), 0) as TotalSpend
    FROM Suppliers s
    LEFT JOIN PurchaseOrders p ON s.SupplierID = p.SupplierID
    GROUP BY s.SupplierID
    ORDER BY s.ReliabilityScore DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict(orient='records')


def get_purchase_orders(limit=200):
    """Return recent purchase orders joined with supplier and material names."""
    conn = sqlite3.connect(db_path)
    query = f"""
    SELECT 
        p.POID,
        s.Name as SupplierName,
        m.Name as MaterialName,
        p.OrderDate,
        p.ExpectedDeliveryDate,
        COALESCE(d.ActualDeliveryDate, 'Pending') as ActualDeliveryDate,
        p.Quantity,
        COALESCE(d.QuantityReceived, 0) as QuantityReceived,
        COALESCE(d.DefectQuantity, 0) as DefectQuantity,
        p.TotalCost,
        CASE 
            WHEN d.ActualDeliveryDate IS NULL THEN 'Pending'
            WHEN julianday(d.ActualDeliveryDate) > julianday(p.ExpectedDeliveryDate) THEN 'Late'
            ELSE 'On-Time'
        END as Status
    FROM PurchaseOrders p
    JOIN Suppliers s ON p.SupplierID = s.SupplierID
    JOIN RawMaterials m ON p.MaterialID = m.MaterialID
    LEFT JOIN Deliveries d ON d.POID = p.POID
    ORDER BY p.OrderDate DESC
    LIMIT {limit}
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict(orient='records')
