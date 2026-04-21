import sqlite3
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import LogisticRegression
import os
from datetime import datetime

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

def calculate_supplier_reliability_scores():
    """
    Calculates reliability scores for all suppliers using the formula:
    reliability_score = (0.4 * otif + 0.3 * (1 / avg_lead_time) + 0.2 * (1 - defect_rate) + 0.1 * cost_efficiency)
    
    Returns a list of suppliers with calculated scores, ranked from highest to lowest.
    """
    conn = sqlite3.connect(db_path)
    
    # Get supplier data with metrics
    query = """
    SELECT 
        s.SupplierID,
        s.Name,
        s.Category,
        COUNT(p.POID) as total_orders,
        SUM(CASE WHEN d.ActualDeliveryDate <= p.ExpectedDeliveryDate AND d.DefectQuantity = 0 THEN 1 ELSE 0 END) as on_time_full,
        AVG(julianday(d.ActualDeliveryDate) - julianday(p.OrderDate)) as avg_lead_time_days,
        SUM(COALESCE(d.DefectQuantity, 0)) as total_defects,
        SUM(d.QuantityReceived) as total_received,
        AVG(p.TotalCost) as avg_cost_per_order
    FROM Suppliers s
    LEFT JOIN PurchaseOrders p ON s.SupplierID = p.SupplierID
    LEFT JOIN Deliveries d ON p.POID = d.POID
    GROUP BY s.SupplierID
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return []
    
    results = []
    
    for idx, row in df.iterrows():
        # Calculate OTIF
        total_orders = row['total_orders'] or 1
        on_time_full = row['on_time_full'] or 0
        otif = (on_time_full / total_orders) * 100 if total_orders > 0 else 0
        
        # Normalize OTIF to 0-1 scale
        otif_normalized = otif / 100
        
        # Lead time component (inverse, with normalization)
        avg_lead_time = row['avg_lead_time_days'] or 30
        lead_time_component = 1 / max(avg_lead_time / 30, 0.1)  # Normalize to 30 days as baseline
        lead_time_component = min(lead_time_component, 1.0)  # Cap at 1.0
        
        # Defect rate component
        total_received = row['total_received'] or 1
        total_defects = row['total_defects'] or 0
        defect_rate = (total_defects / total_received) * 100 if total_received > 0 else 0
        defect_component = 1 - (defect_rate / 100)
        
        # Cost efficiency component (inverse - lower cost = better)
        avg_cost = row['avg_cost_per_order'] or 1000
        # Assume average cost is around 1000 units; efficiency is inverse
        cost_component = min(1000 / max(avg_cost, 1), 1.0)
        
        # Calculate composite reliability score
        reliability_score = (
            0.4 * otif_normalized +
            0.3 * lead_time_component +
            0.2 * defect_component +
            0.1 * cost_component
        )
        
        # Normalize to 0-100 scale
        reliability_score_100 = reliability_score * 100
        
        results.append({
            "supplier_id": int(row['SupplierID']),
            "name": row['Name'],
            "category": row['Category'],
            "reliability_score": round(reliability_score_100, 2),
            "otif": round(otif_normalized * 100, 2),
            "avg_lead_time_days": round(avg_lead_time, 1) if avg_lead_time else 0,
            "defect_rate": round(defect_rate, 2),
            "avg_cost_per_order": round(avg_cost, 2),
            "total_orders": int(total_orders)
        })
    
    # Sort by reliability score descending
    results.sort(key=lambda x: x['reliability_score'], reverse=True)
    return results

def predict_delay_probability(supplier_id, material_id=None):
    """
    Predicts the probability of delay for a supplier based on historical data.
    
    Features:
    - Supplier's historical delay rate
    - Current month/season
    - Lead time trends
    
    Returns: {
        "supplier_id": int,
        "material_id": int or None,
        "delay_probability": float (0-100),
        "risk_level": "LOW" | "MEDIUM" | "HIGH",
        "reasoning": str
    }
    """
    conn = sqlite3.connect(db_path)
    
    # Get supplier delay history
    query = """
    SELECT 
        p.POID,
        p.OrderDate,
        p.ExpectedDeliveryDate,
        d.ActualDeliveryDate,
        CASE WHEN d.ActualDeliveryDate > p.ExpectedDeliveryDate THEN 1 ELSE 0 END as was_delayed,
        julianday(d.ActualDeliveryDate) - julianday(p.OrderDate) as actual_lead_time,
        julianday(p.ExpectedDeliveryDate) - julianday(p.OrderDate) as expected_lead_time
    FROM PurchaseOrders p
    LEFT JOIN Deliveries d ON p.POID = d.POID
    WHERE p.SupplierID = ?
    ORDER BY p.OrderDate DESC
    """
    
    df = pd.read_sql_query(query, conn, params=(supplier_id,))
    conn.close()
    
    if df.empty or len(df) < 2:
        # Not enough data - return neutral prediction
        return {
            "supplier_id": supplier_id,
            "material_id": material_id,
            "delay_probability": 50.0,
            "risk_level": "MEDIUM",
            "reasoning": "Insufficient historical data"
        }
    
    # Calculate historical delay rate
    df['OrderDate'] = pd.to_datetime(df['OrderDate'])
    df['was_delayed'] = pd.to_numeric(df['was_delayed'], errors='coerce').fillna(0)
    
    delay_rate = df['was_delayed'].mean() * 100
    
    # Get current month seasonality
    current_month = datetime.now().month
    recent_orders = df[df['OrderDate'] >= df['OrderDate'].max() - pd.Timedelta(days=90)]
    
    recent_delay_rate = recent_orders['was_delayed'].mean() * 100 if len(recent_orders) > 0 else delay_rate
    
    # Combine factors
    # - 60% weight on historical delay rate
    # - 30% weight on recent trend
    # - 10% weight on time-of-year seasonality
    seasonal_factor = 1.1 if current_month in [11, 12, 1] else 1.0  # Holiday season increases risk
    
    predicted_probability = (
        0.6 * delay_rate +
        0.3 * recent_delay_rate +
        0.1 * (delay_rate * (seasonal_factor - 1) * 100)
    )
    
    # Normalize to 0-100
    predicted_probability = min(max(predicted_probability, 0), 100)
    
    # Determine risk level
    if predicted_probability >= 70:
        risk_level = "HIGH"
    elif predicted_probability >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    reasoning = f"Based on {len(df)} historical orders: {delay_rate:.0f}% historical delays"
    
    return {
        "supplier_id": supplier_id,
        "material_id": material_id,
        "delay_probability": round(predicted_probability, 2),
        "risk_level": risk_level,
        "reasoning": reasoning
    }

def get_procurement_alerts():
    """
    Generates active alerts for procurement risks.
    Returns top 5 most critical alerts to avoid overwhelming users.
    
    Alert criteria:
    1. Suppliers with reliability_score < 60 (unreliable)
    2. Suppliers with HIGH delay risk
    3. Materials below minimum threshold
    """
    alerts = []
    
    # Get supplier reliability data
    suppliers = calculate_supplier_reliability_scores()
    
    # Check for low reliability suppliers (< 60)
    for supplier in suppliers:
        if supplier['reliability_score'] < 60:
            severity = "HIGH" if supplier['reliability_score'] < 40 else "MEDIUM"
            alerts.append({
                "type": "LOW_RELIABILITY",
                "severity": severity,
                "supplier_id": supplier['supplier_id'],
                "supplier_name": supplier['name'],
                "message": f"⚠ Supplier '{supplier['name']}' reliability score: {supplier['reliability_score']:.0f}",
                "details": f"OTIF: {supplier['otif']:.0f}%, Lead Time: {supplier['avg_lead_time_days']:.0f} days, Defect Rate: {supplier['defect_rate']:.1f}%"
            })
    
    # Check for material stock below threshold
    conn = sqlite3.connect(db_path)
    stock_query = """
    SELECT MaterialID, Name, CurrentStock, MinThreshold
    FROM RawMaterials
    WHERE CurrentStock < MinThreshold
    ORDER BY (MinThreshold - CurrentStock) DESC
    LIMIT 5
    """
    df = pd.read_sql_query(stock_query, conn)
    conn.close()
    
    for idx, row in df.iterrows():
        alerts.append({
            "type": "LOW_STOCK",
            "severity": "MEDIUM",
            "material_id": int(row['MaterialID']),
            "material_name": row['Name'],
            "message": f"📦 Low stock: '{row['Name']}' ({row['CurrentStock']} remaining)",
            "details": f"Current: {row['CurrentStock']} | Minimum: {row['MinThreshold']}"
        })
    
    # Sort by severity (HIGH first, then MEDIUM)
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    alerts.sort(key=lambda x: severity_order.get(x['severity'], 3))
    
    # LIMIT to top 5 most critical alerts to avoid overwhelming the user
    return alerts[:5]
