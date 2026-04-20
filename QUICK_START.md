# 🚀 Quick Start Guide - New Features

## Running the System

### Backend (Flask API)
```bash
cd c:\Users\aadhy\procurement-management-system
python backend/app.py
```
Server runs on: **http://localhost:5001**

### Frontend (React + Vite)
```bash
cd c:\Users\aadhy\procurement-management-system\frontend
npm run dev
```
Frontend runs on: **http://localhost:5174**

---

## Using the New Features

### 1️⃣ Supplier Reliability Leaderboard

**Where to find it:**
- Click **"Leaderboard"** in the sidebar navigation
- Or scroll down on the Dashboard

**What you see:**
- All suppliers ranked by reliability score (0-100)
- Color-coded badges:
  - 🟢 **Green (80+)**: Excellent
  - 🔵 **Blue (70-79)**: Good
  - 🟠 **Orange (60-69)**: Fair
  - 🔴 **Red (<60)**: Poor

**What the score means:**
- 40% On-Time In-Full delivery
- 30% Fast lead times
- 20% Quality (low defects)
- 10% Cost efficiency

**Top 3 get medals:** 🥇🥈🥉

---

### 2️⃣ Delay Risk Prediction

**Where to find it:**
- Currently exposed via API: `GET /api/predict/delay/<supplier_id>`
- Example: `http://localhost:5001/api/predict/delay/1`

**What it tells you:**
```
{
  "delay_probability": 31.9,    // % chance of delay
  "risk_level": "LOW",           // LOW | MEDIUM | HIGH
  "reasoning": "Based on 91 historical orders..."
}
```

**How it works:**
- Analyzes past delivery performance
- Checks recent trends (last 90 days)
- Accounts for seasonal factors
- Returns probability as percentage

---

### 3️⃣ Procurement Risk Alerts

**Where to find it:**
- Top of the **Dashboard** page
- Shows immediately on load

**Alert Types:**

| Type | Severity | What it means |
|------|----------|--------------|
| 🔴 Low Reliability | HIGH/MEDIUM | Supplier score dropped below 60 |
| ⏰ High Delay Risk | HIGH | Supplier has >70% delay probability |
| ⚠️ Low Stock | MEDIUM | Material below minimum threshold |

**Example Alert:**
```
⚠ Supplier 'Supplier B' reliability score dropped to 52.1
OTIF: 25%, Lead Time: 23.5 days, Defect Rate: 5.2%
```

**Alerts are sorted by:**
1. Severity (HIGH → MEDIUM → LOW)
2. Most critical issues first
3. Refreshes when data changes

---

## API Reference

### New Endpoints

#### 1. Get Supplier Rankings
```
GET /api/suppliers/ranking
```
**Response:**
```json
[
  {
    "supplier_id": 1,
    "name": "Supplier D",
    "category": "Raw Materials",
    "reliability_score": 53.29,
    "otif": 45.2,
    "avg_lead_time_days": 18.5,
    "defect_rate": 3.2,
    "avg_cost_per_order": 25000,
    "total_orders": 89
  }
]
```

#### 2. Predict Supplier Delay
```
GET /api/predict/delay/<supplier_id>?material_id=<optional>
```
**Response:**
```json
{
  "supplier_id": 1,
  "material_id": null,
  "delay_probability": 31.9,
  "risk_level": "LOW",
  "reasoning": "Based on 91 historical orders: 41% historical delays"
}
```

#### 3. Get Active Alerts
```
GET /api/alerts
```
**Response:**
```json
[
  {
    "type": "LOW_RELIABILITY",
    "severity": "MEDIUM",
    "supplier_id": 2,
    "supplier_name": "Supplier B",
    "message": "⚠ Supplier 'Supplier B' reliability score dropped to 52.1",
    "details": "OTIF: 25%, Lead Time: 23.5 days, Defect Rate: 5.2%"
  }
]
```

---

## Understanding the Metrics

### Reliability Score (0-100)
**Components:**
- **OTIF %**: How often supplier delivers on-time and in-full
  - 100% OTIF = excellent
  - <50% OTIF = unreliable

- **Lead Time (days)**: Average time from order to delivery
  - 10 days = good
  - 30+ days = slow

- **Defect Rate %**: Percentage of faulty items
  - <2% = excellent quality
  - >5% = quality issues

- **Cost $/order**: Average cost per purchase order
  - Lower is better for cost efficiency

### Delay Probability (0-100%)
**What it measures:**
- Likelihood supplier will miss promised delivery date
- Based on historical performance
- Adjusts for recent trends
- Considers seasonal patterns

**Risk Levels:**
- **LOW** (0-40%): Usually delivers on-time
- **MEDIUM** (40-70%): Sometimes delayed
- **HIGH** (70-100%): Frequently delayed

---

## Troubleshooting

### Alerts not showing?
- Check if database has data (run generate_mock_data.py first)
- Verify backend is running on port 5001
- Check browser console for errors (F12)

### Empty leaderboard?
- Need supplier data in database
- Run: `python backend/generate_mock_data.py`
- Wait for backend to process

### API returning errors?
- Ensure Flask server is running: `python backend/app.py`
- Check port 5001 is not in use
- Look at server terminal for error messages

---

## Example Workflow

1. **Open Dashboard** → See alerts at top
2. **Check KPIs** → Overall procurement health
3. **Click Leaderboard** → Identify best/worst suppliers
4. **Review alerts** → Understand which suppliers need attention
5. **Plan procurement** → Prioritize reliable suppliers
6. **Monitor delays** → Use delay predictions to adjust schedules

---

## Files Modified

### Backend
- ✅ `backend/app.py` - Added 3 new API routes
- ✅ `backend/ml_models.py` - Added scoring, prediction, alert functions

### Frontend
- ✅ `frontend/src/App.jsx` - Integrated new components
- ✅ `frontend/src/components/AlertsBanner.jsx` - New alert display
- ✅ `frontend/src/components/SupplierLeaderboard.jsx` - New leaderboard
- ✅ `frontend/src/index.css` - Added styling for new features

---

## Performance Notes

- **Supplier Ranking**: Calculated on-demand (real-time)
- **Delay Prediction**: Uses historical data (fast)
- **Alerts**: Generated on-demand (comprehensive scan)
- Database queries are optimized with proper JOINs

---

Enjoy your enhanced procurement system! 🎉
