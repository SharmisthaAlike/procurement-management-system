import React, { useState, useEffect } from 'react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer,
  LineChart, Line, ScatterChart, Scatter, ZAxis, Legend,
} from 'recharts';
import {
  LayoutDashboard, Package, Users, Truck, AlertTriangle, DollarSign,
  Activity, ShieldCheck, Clock, TrendingDown, BarChart2, Upload,
  ClipboardList, AlertCircle, RefreshCw, CheckCircle2, Zap, Trophy
} from 'lucide-react';

import KPICard      from './components/KPICard';
import DataListView from './components/DataListView';
import DataFormModal from './components/DataFormModal';
import AlertsBanner from './components/AlertsBanner';
import SupplierLeaderboard from './components/SupplierLeaderboard';
import CSVUpload    from './components/CSVUpload';
import './index.css';

const API_BASE = 'http://localhost:5001/api';

/* ── Custom Recharts Tooltip ────────────────────────────────────────── */
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'rgba(8,13,26,0.95)', border: '1px solid rgba(255,255,255,0.12)',
      borderRadius: 10, padding: '0.75rem 1rem', fontSize: '0.82rem',
    }}>
      <p style={{ color: '#94a3b8', marginBottom: '0.35rem', fontWeight: 600 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color, marginBottom: '0.15rem' }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toLocaleString() : p.value}</strong>
        </p>
      ))}
    </div>
  );
};

/* ── Nav config ─────────────────────────────────────────────────────── */
const NAV = [
  { id: 'dashboard',   label: 'Dashboard',        icon: LayoutDashboard, section: 'ANALYTICS' },
  { id: 'orders',      label: 'Purchase Orders',   icon: ClipboardList,   section: 'ANALYTICS' },
  { id: 'materials',   label: 'Raw Materials',     icon: Package,         section: 'MASTER DATA' },
  { id: 'suppliers',   label: 'Suppliers',         icon: Users,           section: 'MASTER DATA' },
  { id: 'import',      label: 'Import CSV',        icon: Upload,          section: 'TOOLS' },
];

/* ══════════════════════════════════════════════════════════════════════
   APP
══════════════════════════════════════════════════════════════════════ */
function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  
  const [kpis, setKpis] = useState({});
  const [materials, setMaterials] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [supplierRankings, setSupplierRankings] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [selectedMaterial, setSelectedMaterial] = useState('');
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isMaterialModalOpen, setMaterialModal] = useState(false);
  const [isSupplierModalOpen, setSupplierModal] = useState(false);

  useEffect(() => { fetchAll(); }, []);
  useEffect(() => { if (selectedMaterial) fetchForecast(selectedMaterial); }, [selectedMaterial]);

  /* ── Data Fetching ── */
  const fetchAll = async (isRefresh = false) => {
    isRefresh ? setRefreshing(true) : setLoading(true);
    try {
        const [kpiRes, matRes, supRes, rankRes, alertRes, ordRes] = await Promise.all([
          fetch(`${API_BASE}/kpis`),
          fetch(`${API_BASE}/materials`),
          fetch(`${API_BASE}/suppliers`),
          fetch(`${API_BASE}/suppliers/ranking`),
          fetch(`${API_BASE}/alerts`),
          fetch(`${API_BASE}/purchase-orders`)
        ]);
        
        const kpiData = await kpiRes.json();
        const matData = await matRes.json();
        const supData = await supRes.json();
        const rankData = await rankRes.json();
        const alertData = await alertRes.json();
        const ordData = await ordRes.json();

        setKpis(kpiData);
        setMaterials(matData);
        setSuppliers(supData);
        setSupplierRankings(Array.isArray(rankData) ? rankData : []);
        setAlerts(Array.isArray(alertData) ? alertData : []);
        setOrders(ordData);
        
        if (matData.length > 0 && !selectedMaterial) {
            setSelectedMaterial(matData[0].MaterialID);
        }
    } catch (error) {
        console.error("Error fetching data:", error);
    }
    isRefresh ? setRefreshing(false) : setLoading(false);
  };

  const fetchForecast = async (id) => {
    try {
      const res  = await fetch(`${API_BASE}/forecast/${id}`);
      const data = await res.json();
      setForecast(data);
    } catch (e) { console.error(e); }
  };

  /* ── CRUD ── */
  const handleCreateMaterial = async (data) => {
    try {
      await fetch(`${API_BASE}/materials`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      setMaterialModal(false);
      fetchAll(true);
    } catch (e) { console.error(e); }
  };

  const handleDeleteMaterial = async (row) => {
    if (!window.confirm(`Delete "${row.Name}"?`)) return;
    const res  = await fetch(`${API_BASE}/materials/${row.MaterialID}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.error) alert(data.error);
    else fetchAll(true);
  };

  const handleCreateSupplier = async (data) => {
    try {
      await fetch(`${API_BASE}/suppliers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      setSupplierModal(false);
      fetchAll(true);
    } catch (e) { console.error(e); }
  };

  const handleDeleteSupplier = async (row) => {
    if (!row.SupplierID) { alert('Supplier ID not available.'); return; }
    if (!window.confirm(`Delete supplier "${row.Name}"?`)) return;
    const res  = await fetch(`${API_BASE}/suppliers/${row.SupplierID}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.error) alert(data.error);
    else fetchAll(true);
  };

  /* ── Derived chart data ── */
  const combinedChartData = [];
  if (forecast && !forecast.error) {
    forecast.historical.forEach(h =>
      combinedChartData.push({ name: h.month, Actual: h.actual_demand, Forecast: null })
    );
    forecast.forecast.forEach(f =>
      combinedChartData.push({ name: f.month, Actual: null, Forecast: f.predicted_demand })
    );
  }

  /* ── Loading screen ── */
  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-logo" />
        <p className="loading-text">Loading Procurement Intelligence...</p>
      </div>
    );
  }

  /* ══════════════════════════════════════════════════════════════════
     DASHBOARD VIEW
  ══════════════════════════════════════════════════════════════════ */
  const renderDashboard = () => {
    const hasStockout = kpis.stockout_risk_count > 0;

    return (
      <div className="dashboard-container">
        {/* Header */}
        <div className="page-header animate-fade-in delay-1">
          <div>
            <h1 className="page-header__title">Procurement Intelligence</h1>
            <p className="page-header__sub">P2 Reliability Dashboard · Real-time supply chain health</p>
          </div>
          <div className="page-header__badges">
            <span className="badge badge--blue">OTIF Tracking</span>
            <span className="badge badge--purple">ML Forecasting</span>
            <span className="badge badge--green">Live KPIs</span>
            <button
              className="btn-primary"
              style={{ marginLeft: '0.5rem' }}
              onClick={() => fetchAll(true)}
              disabled={refreshing}
            >
              <RefreshCw size={14} style={{ animation: refreshing ? 'spin 0.7s linear infinite' : 'none' }} />
              Refresh
            </button>
          </div>
        </div>

        {/* Risk Alert Banner */}
        <AlertsBanner alerts={alerts} />

        {hasStockout && (
          <div className="risk-banner animate-fade-in">
            <AlertTriangle size={22} color="var(--accent-red)" className="risk-banner__icon" />
            <div className="risk-banner__text">
              <strong>⚠ {kpis.stockout_risk_count} Material{kpis.stockout_risk_count > 1 ? 's' : ''} at Stockout Risk</strong>
              {kpis.risk_materials && (
                <span> · {kpis.risk_materials}</span>
              )}
            </div>
          </div>
        )}

        {/* KPI Row 1 — Core Reliability */}
        <div className="kpi-grid animate-fade-in delay-2">
          <KPICard
            title="OTIF Rate"
            value={`${kpis.otif_rate}%`}
            icon={CheckCircle2}
            color="var(--accent-green)"
            trend={kpis.otif_rate >= 85 ? 'up' : 'down'}
            trendGood={true}
            status={kpis.otif_rate >= 85 ? 'good' : kpis.otif_rate >= 70 ? 'warn' : 'danger'}
            subtitle={kpis.otif_rate < 85 ? 'Target: ≥ 85%' : null}
          />
          <KPICard
            title="Avg Lead Time"
            value={`${kpis.avg_lead_time_days}d`}
            icon={Clock}
            color="var(--accent-sky)"
            trend={kpis.avg_lead_time_days <= 20 ? 'down' : 'up'}
            trendGood={false}
            status={kpis.avg_lead_time_days <= 20 ? 'good' : kpis.avg_lead_time_days <= 30 ? 'warn' : 'danger'}
          />
          <KPICard
            title="Late Delivery Rate"
            value={`${kpis.late_delivery_rate}%`}
            icon={TrendingDown}
            color="var(--accent-red)"
            trend={kpis.late_delivery_rate <= 15 ? 'down' : 'up'}
            trendGood={false}
            status={kpis.late_delivery_rate <= 15 ? 'good' : kpis.late_delivery_rate <= 30 ? 'warn' : 'danger'}
          />
          <KPICard
            title="Defect Rate"
            value={`${kpis.defect_rate}%`}
            icon={ShieldCheck}
            color="var(--accent-amber)"
            trend={kpis.defect_rate <= 5 ? 'down' : 'up'}
            trendGood={false}
            status={kpis.defect_rate <= 5 ? 'good' : kpis.defect_rate <= 10 ? 'warn' : 'danger'}
          />
          <KPICard
            title="Stockout Risk"
            value={kpis.stockout_risk_count}
            icon={AlertTriangle}
            color={kpis.stockout_risk_count > 0 ? 'var(--accent-red)' : 'var(--accent-green)'}
            status={kpis.stockout_risk_count === 0 ? 'good' : kpis.stockout_risk_count <= 3 ? 'warn' : 'danger'}
            subtitle={kpis.stockout_risk_count > 0 ? 'Items below min threshold' : 'All stock levels healthy'}
          />
        </div>

        {/* KPI Row 2 — Financial & Efficiency */}
        <div className="kpi-grid kpi-grid--row2 animate-fade-in delay-3">
          <KPICard
            title="Supplier Fill Rate"
            value={`${kpis.fill_rate}%`}
            icon={Truck}
            color="var(--accent-teal)"
            trend={kpis.fill_rate >= 95 ? 'up' : 'down'}
            trendGood={true}
            status={kpis.fill_rate >= 95 ? 'good' : kpis.fill_rate >= 85 ? 'warn' : 'danger'}
          />
          <KPICard
            title="Avg Delay per Order"
            value={`${kpis.avg_delay_days}d`}
            icon={Activity}
            color="var(--accent-purple)"
            trend={kpis.avg_delay_days <= 2 ? 'down' : 'up'}
            trendGood={false}
            status={kpis.avg_delay_days <= 2 ? 'good' : kpis.avg_delay_days <= 5 ? 'warn' : 'danger'}
            subtitle="Avg days past expected delivery"
          />
          <KPICard
            title="Spend Concentration"
            value={`${kpis.spend_concentration_pct}%`}
            icon={Zap}
            color="var(--accent-indigo)"
            trend={kpis.spend_concentration_pct <= 30 ? 'down' : 'up'}
            trendGood={false}
            status={kpis.spend_concentration_pct <= 30 ? 'good' : kpis.spend_concentration_pct <= 50 ? 'warn' : 'danger'}
            subtitle={`Top: ${kpis.top_supplier_name}`}
          />
          <KPICard
            title="Avg Cost / Order"
            value={`$${Number(kpis.avg_cost_per_order).toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
            icon={DollarSign}
            color="var(--accent-green)"
            trend="neutral"
          />
          <KPICard
            title="Total Procurement Spend"
            value={`$${(kpis.total_spend / 1000).toFixed(0)}K`}
            icon={BarChart2}
            color="var(--accent-blue)"
            trend="neutral"
            subtitle="Trailing 12 months"
          />
        </div>

        {/* Charts Row 1 — Forecast + Delivery Trend */}
        <div className="charts-grid animate-fade-in delay-4">
          {/* Demand Forecast */}
          <div className="glass-card">
            <div className="chart-header">
              <div className="chart-header__left">
                <h2 className="chart-title">Demand Forecast</h2>
                <span className="chart-subtitle">Historical vs ML-predicted monthly demand</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span className="ml-badge">🤖 Linear Regression</span>
                <select
                  className="select-material"
                  value={selectedMaterial}
                  onChange={(e) => setSelectedMaterial(e.target.value)}
                >
                  {materials.map(m => (
                    <option key={m.MaterialID} value={m.MaterialID}>
                      {m.Name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div style={{ width: '100%', height: 280 }}>
              {forecast?.error ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
                  <AlertCircle size={16} style={{ marginRight: '0.5rem' }} />
                  {forecast.error}
                </div>
              ) : (
                <ResponsiveContainer>
                  <LineChart data={combinedChartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="name" stroke="var(--text-muted)" tick={{ fontSize: 11 }} />
                    <YAxis stroke="var(--text-muted)" tick={{ fontSize: 11 }} />
                    <RechartsTooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ fontSize: '0.8rem', color: 'var(--text-muted)' }} />
                    <Line type="monotone" dataKey="Actual" stroke="var(--accent-blue)" strokeWidth={2.5} dot={{ r: 3 }} connectNulls={false} />
                    <Line type="monotone" dataKey="Forecast" stroke="var(--accent-purple)" strokeWidth={2.5} strokeDasharray="6 3" dot={{ r: 5 }} connectNulls={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Delivery Trend */}
          <div className="glass-card">
            <div className="chart-header">
              <div className="chart-header__left">
                <h2 className="chart-title">On-Time vs Late Deliveries</h2>
                <span className="chart-subtitle">Monthly trend (last 12 months)</span>
              </div>
            </div>
            <div style={{ width: '100%', height: 280 }}>
              <ResponsiveContainer>
                <AreaChart data={kpis.delivery_trend || []} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gradOnTime" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="var(--accent-green)"  stopOpacity={0.3} />
                      <stop offset="95%" stopColor="var(--accent-green)"  stopOpacity={0.02} />
                    </linearGradient>
                    <linearGradient id="gradLate" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="var(--accent-red)"    stopOpacity={0.3} />
                      <stop offset="95%" stopColor="var(--accent-red)"    stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="Month" stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                  <YAxis stroke="var(--text-muted)" tick={{ fontSize: 11 }} />
                  <RechartsTooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '0.8rem', color: 'var(--text-muted)' }} />
                  <Area type="monotone" dataKey="OnTime" name="On-Time" stroke="var(--accent-green)"  fill="url(#gradOnTime)" strokeWidth={2} />
                  <Area type="monotone" dataKey="Late"   name="Late"    stroke="var(--accent-red)"    fill="url(#gradLate)"   strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Charts Row 2 — Supplier Reliability + Spend */}
        <div className="charts-grid charts-grid--equal animate-fade-in delay-5">
          {/* Spend by Supplier */}
          <div className="glass-card">
            <div className="chart-header">
              <div className="chart-header__left">
                <h2 className="chart-title">Spend by Supplier</h2>
                <span className="chart-subtitle">Top 8 by total procurement value</span>
              </div>
            </div>
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer>
                <BarChart data={kpis.spend_by_supplier || []} layout="vertical" margin={{ top: 0, right: 20, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
                  <XAxis type="number" stroke="var(--text-muted)" tick={{ fontSize: 10 }}
                    tickFormatter={v => `$${(v/1000).toFixed(0)}K`} />
                  <YAxis type="category" dataKey="Name" stroke="var(--text-muted)" tick={{ fontSize: 10 }} width={80} />
                  <RechartsTooltip content={<CustomTooltip />} formatter={(v) => [`$${Number(v).toLocaleString()}`, 'Spend']} />
                  <Bar dataKey="TotalSpend" name="Spend" fill="var(--accent-indigo)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Supplier Reliability Scatter */}
          <div className="glass-card">
            <div className="chart-header">
              <div className="chart-header__left">
                <h2 className="chart-title">Supplier Risk Matrix</h2>
                <span className="chart-subtitle">Volume vs Reliability · Size = spend</span>
              </div>
            </div>
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer>
                <ScatterChart margin={{ top: 10, right: 20, left: -10, bottom: 10 }}>
                  <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                  <XAxis type="number" dataKey="OrderCount"      name="Orders"      stroke="var(--text-muted)" tick={{ fontSize: 10 }} label={{ value: 'PO Count', position: 'insideBottom', offset: -4, fill: 'var(--text-muted)', fontSize: 10 }} />
                  <YAxis type="number" dataKey="ReliabilityScore" name="Reliability" domain={[0.6, 1]} stroke="var(--text-muted)" tick={{ fontSize: 10 }} label={{ value: 'Reliability', angle: -90, position: 'insideLeft', fill: 'var(--text-muted)', fontSize: 10 }} />
                  <ZAxis type="number" dataKey="TotalSpend" range={[40, 300]} name="Spend" />
                  <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} content={<CustomTooltip />} />
                  <Scatter name="Suppliers" data={suppliers} fill="var(--accent-teal)" fillOpacity={0.75} />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <SupplierLeaderboard suppliers={supplierRankings} />
      </div>
    );
  };

  /* ══════════════════════════════════════════════════════════════════
     PURCHASE ORDERS VIEW
  ══════════════════════════════════════════════════════════════════ */
  const renderOrders = () => (
    <DataListView
      title="Purchase Orders"
      columns={[
        { label: 'PO #',       key: 'POID' },
        { label: 'Supplier',   key: 'SupplierName' },
        { label: 'Material',   key: 'MaterialName' },
        { label: 'Order Date', key: 'OrderDate' },
        { label: 'Expected',   key: 'ExpectedDeliveryDate' },
        { label: 'Actual',     key: 'ActualDeliveryDate' },
        { label: 'Qty',        key: 'Quantity' },
        { label: 'Rcvd',       key: 'QuantityReceived' },
        { label: 'Defects',    key: 'DefectQuantity' },
        {
          label: 'Status',
          key: 'Status',
          render: (val) => (
            <span className={`status-badge status-badge--${val === 'On-Time' ? 'on-time' : val === 'Late' ? 'late' : 'pending'}`}>
              {val}
            </span>
          ),
        },
        {
          label: 'Cost',
          key: 'TotalCost',
          render: (val) => `$${Number(val).toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
        },
      ]}
      data={orders}
      onAdd={() => {}}
      onDelete={() => {}}
    />
  );

  /* ══════════════════════════════════════════════════════════════════
     SIDEBAR
  ══════════════════════════════════════════════════════════════════ */
  const renderSidebar = () => {
    const sections = [...new Set(NAV.map(n => n.section))];
    return (
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand__logo">PS</div>
          <div className="sidebar-brand__text">
            <span className="sidebar-brand__name">Procurement OS</span>
            <span className="sidebar-brand__tagline">Supply Chain Intelligence</span>
          </div>
        </div>
        {sections.map(section => (
          <React.Fragment key={section}>
            <div className="sidebar-section-label">{section}</div>
            {NAV.filter(n => n.section === section).map(item => (
              <button
                key={item.id}
                className={`nav-item ${currentView === item.id ? 'active' : ''}`}
                onClick={() => setCurrentView(item.id)}
              >
                <div className="nav-item__icon">
                  <item.icon size={16} />
                </div>
                {item.label}
              </button>
            ))}
          </React.Fragment>
        ))}
      </aside>
    );
  };

  /* ══════════════════════════════════════════════════════════════════
     RENDER
  ══════════════════════════════════════════════════════════════════ */
  return (
    <div className="app-layout">
      {renderSidebar()}

      <main className="main-content">
        {currentView === 'dashboard' && renderDashboard()}

        {currentView === 'orders' && renderOrders()}

        {currentView === 'materials' && (
          <DataListView
            title="Raw Materials"
            columns={[
              { label: 'ID',            key: 'MaterialID' },
              { label: 'Name',          key: 'Name' },
              { label: 'Category',      key: 'Category' },
              {
                label: 'Stock Level',
                key: 'CurrentStock',
                render: (val, row) => {
                  const atRisk = row.MinThreshold > 0 && val < row.MinThreshold;
                  return (
                    <span style={{ color: atRisk ? 'var(--accent-red)' : 'inherit', fontWeight: atRisk ? 700 : 400 }}>
                      {val} {atRisk && '⚠'}
                    </span>
                  );
                },
              },
              { label: 'Min Threshold', key: 'MinThreshold' },
              {
                label: 'Cost/Unit',
                key: 'CostPerUnit',
                render: (val) => `$${Number(val).toFixed(2)}`,
              },
            ]}
            data={materials}
            onAdd={() => setMaterialModal(true)}
            onDelete={handleDeleteMaterial}
          />
        )}

        {currentView === 'suppliers' && (
          <DataListView
            title="Suppliers Hub"
            columns={[
              { label: 'Name',       key: 'Name' },
              { label: 'Category',   key: 'Category' },
              {
                label: 'Reliability',
                key: 'ReliabilityScore',
                render: (val) => {
                  const pct = (val * 100).toFixed(0);
                  const col = val >= 0.9 ? 'var(--accent-green)' : val >= 0.8 ? 'var(--accent-amber)' : 'var(--accent-red)';
                  return <span style={{ color: col, fontWeight: 700 }}>{pct}%</span>;
                },
              },
              { label: 'Total Orders', key: 'OrderCount' },
              {
                label: 'Total Spend',
                key: 'TotalSpend',
                render: (val) => `$${Number(val).toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
              },
            ]}
            data={suppliers}
            onAdd={() => setSupplierModal(true)}
            onDelete={handleDeleteSupplier}
          />
        )}

        {currentView === 'import' && (
          <CSVUpload onSuccess={() => fetchAll(true)} />
        )}
      </main>

      {/* Modals */}
      <DataFormModal
        title="Add Raw Material"
        isOpen={isMaterialModalOpen}
        onClose={() => setMaterialModal(false)}
        onSubmit={handleCreateMaterial}
        fields={[
          { label: 'Material Name', key: 'Name',         required: true },
          { label: 'Category',      key: 'Category',     required: true },
          { label: 'Initial Stock', key: 'CurrentStock', type: 'number' },
          { label: 'Min Threshold', key: 'MinThreshold', type: 'number' },
          { label: 'Cost Per Unit ($)', key: 'CostPerUnit', type: 'number' },
        ]}
      />

      <DataFormModal
        title="Add Supplier"
        isOpen={isSupplierModalOpen}
        onClose={() => setSupplierModal(false)}
        onSubmit={handleCreateSupplier}
        fields={[
          { label: 'Supplier Name',              key: 'Name',             required: true },
          { label: 'Category',                   key: 'Category',         required: true },
          { label: 'Reliability Score (0–1)',    key: 'ReliabilityScore', type: 'number' },
        ]}
      />
    </div>
  );
}

export default App;
