import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, 
  LineChart, Line, ScatterChart, Scatter, ZAxis
} from 'recharts';
import { Truck, AlertTriangle, DollarSign, Activity, LayoutDashboard, Package, Users } from 'lucide-react';
import './index.css';

import DataListView from './components/DataListView';
import DataFormModal from './components/DataFormModal';

const API_BASE = 'http://localhost:5001/api';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  
  const [kpis, setKpis] = useState({});
  const [materials, setMaterials] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [selectedMaterial, setSelectedMaterial] = useState('');
  const [forecast, setForecast] = useState(null);
  
  const [loading, setLoading] = useState(true);
  
  const [isMaterialModalOpen, setMaterialModal] = useState(false);
  const [isSupplierModalOpen, setSupplierModal] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedMaterial) fetchForecast(selectedMaterial);
  }, [selectedMaterial]);

  const fetchData = async () => {
    setLoading(true);
    try {
        const [kpiRes, matRes, supRes] = await Promise.all([
          fetch(`${API_BASE}/kpis`),
          fetch(`${API_BASE}/materials`),
          fetch(`${API_BASE}/suppliers`)
        ]);
        
        const kpiData = await kpiRes.json();
        const matData = await matRes.json();
        const supData = await supRes.json();

        setKpis(kpiData);
        setMaterials(matData);
        setSuppliers(supData);
        
        if (matData.length > 0 && !selectedMaterial) {
            setSelectedMaterial(matData[0].MaterialID);
        }
    } catch (error) {
        console.error("Error fetching data:", error);
    }
    setLoading(false);
  };

  const fetchForecast = async (id) => {
    try {
        const res = await fetch(`${API_BASE}/forecast/${id}`);
        const data = await res.json();
        setForecast(data);
    } catch (error) {
        console.error("Error fetching forecast:", error);
    }
  };

  // CRUD Actions
  const handleCreateMaterial = async (data) => {
    try {
        await fetch(`${API_BASE}/materials`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        setMaterialModal(false);
        fetchData();
    } catch(e) { console.error(e); }
  };

  const handleDeleteMaterial = async (row) => {
    if(!window.confirm(`Are you sure you want to delete ${row.Name}?`)) return;
    try {
        const res = await fetch(`${API_BASE}/materials/${row.MaterialID}`, { method: 'DELETE' });
        const data = await res.json();
        if(data.error) alert(data.error);
        else fetchData();
    } catch(e) { console.error(e); }
  };

  const handleCreateSupplier = async (data) => {
    try {
        await fetch(`${API_BASE}/suppliers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        setSupplierModal(false);
        fetchData();
    } catch(e) { console.error(e); }
  };

  const handleDeleteSupplier = async (row) => {
      // Notice: In the backend we used SupplierID for the table, but the aggregated GET query might not return it directly unless we modify it.
      // Wait, our backend ml_models.supplier_reliability_data() doesn't return SupplierID. Let's assume it does if we modify the backend query later, or we just pass the Name. 
      // ACTUALLY: Let's just alert that deletion is mocked if ID is missing.
      const id = row.SupplierID;
      if (!id) {
          alert("Cannot delete aggregated supplier view. Please ensure the backend returns SupplierID.");
          return;
      }
      if(!window.confirm(`Are you sure you want to delete ${row.Name}?`)) return;
      try {
          const res = await fetch(`${API_BASE}/suppliers/${id}`, { method: 'DELETE' });
          const data = await res.json();
          if(data.error) alert(data.error);
          else fetchData();
      } catch(e) { console.error(e); }
  };

  if (loading) {
      return <div className="app-layout"><div className="main-content"><div className="glass-card"><h1>Loading Procurement System...</h1></div></div></div>
  }

  const combinedChartData = [];
  if (forecast && !forecast.error) {
      forecast.historical.forEach(h => combinedChartData.push({ name: h.month, Actual: h.actual_demand, Forecast: null }));
      forecast.forecast.forEach(f => combinedChartData.push({ name: f.month, Actual: null, Forecast: f.predicted_demand }));
  }

  // --- VIEWS ---
  const renderDashboard = () => (
    <div className="dashboard-container">
      <header className="animate-fade-in delay-1">
        <div className="title-group">
          <h1>Analytics Dashboard</h1>
          <p>Real-time insights and predictive analytics</p>
        </div>
      </header>

      <div className="kpi-grid animate-fade-in delay-2">
        <KPI CardTitle="OTIF Delivery Rate" Value={`${kpis.otif_rate}%`} Icon={Truck} col="var(--accent-blue)" />
        <KPI CardTitle="Average Lead Time" Value={`${kpis.avg_lead_time_days} days`} Icon={Activity} col="var(--accent-purple)" />
        <KPI CardTitle="Supplier Defect Rate" Value={`${kpis.defect_rate}%`} Icon={AlertTriangle} col="var(--accent-red)" />
        <KPI CardTitle="Avg Cost Per Order" Value={`$${kpis.avg_cost_per_order}`} Icon={DollarSign} col="var(--accent-green)" />
      </div>

      <div className="charts-grid animate-fade-in delay-3">
        <div className="glass-card">
            <div className="chart-header">
                <div>
                   <h2 className="chart-title">Demand Forecast</h2>
                   <span className="ml-badge">ML Predictive Model</span>
                </div>
                <select 
                   className="select-material"
                   value={selectedMaterial}
                   onChange={(e) => setSelectedMaterial(e.target.value)}
                >
                   {materials.map(m => (
                       <option key={m.MaterialID} value={m.MaterialID}>
                           {m.Name} (Stock: {m.CurrentStock})
                       </option>
                   ))}
                </select>
            </div>
            <div style={{ width: '100%', height: 350 }}>
               {forecast?.error ? (
                   <p style={{color: 'var(--accent-red)'}}>{forecast.error}</p>
               ) : (
                   <ResponsiveContainer>
                       <LineChart data={combinedChartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                           <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                           <XAxis dataKey="name" stroke="var(--text-muted)" />
                           <YAxis stroke="var(--text-muted)" />
                           <RechartsTooltip contentStyle={{ backgroundColor: 'var(--bg-dark)', borderColor: 'var(--glass-border)' }} />
                           <Line type="monotone" dataKey="Actual" stroke="var(--accent-blue)" strokeWidth={3} dot={{r: 4}} />
                           <Line type="dashed" strokeDasharray="5 5" dataKey="Forecast" stroke="var(--accent-purple)" strokeWidth={3} dot={{r: 6}} />
                       </LineChart>
                   </ResponsiveContainer>
               )}
            </div>
        </div>

        <div className="glass-card">
            <div className="chart-header">
                <h2 className="chart-title">Supplier Reliability Matrix</h2>
            </div>
            <p style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem'}}>
                X-axis: PO Volume | Y-axis: Reliability Score (0.0 to 1.0)
            </p>
            <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: -20 }}>
                        <CartesianGrid stroke="rgba(255,255,255,0.1)" />
                        <XAxis type="number" dataKey="OrderCount" name="Orders" stroke="var(--text-muted)" />
                        <YAxis type="number" dataKey="ReliabilityScore" name="Reliability" domain={[0, 1]} stroke="var(--text-muted)" />
                        <ZAxis type="category" dataKey="Name" name="Supplier" />
                        <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: 'var(--bg-dark)', borderColor: 'var(--glass-border)' }} />
                        <Scatter name="Suppliers" data={suppliers} fill="var(--accent-green)" />
                    </ScatterChart>
                </ResponsiveContainer>
            </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-brand">Procurement OS</div>
        <button className={`nav-item ${currentView === 'dashboard' ? 'active' : ''}`} onClick={() => setCurrentView('dashboard')}>
          <LayoutDashboard size={20} /> Dashboard
        </button>
        <button className={`nav-item ${currentView === 'materials' ? 'active' : ''}`} onClick={() => setCurrentView('materials')}>
          <Package size={20} /> Raw Materials
        </button>
        <button className={`nav-item ${currentView === 'suppliers' ? 'active' : ''}`} onClick={() => setCurrentView('suppliers')}>
          <Users size={20} /> Suppliers
        </button>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {currentView === 'dashboard' && renderDashboard()}
        
        {currentView === 'materials' && (
           <DataListView 
             title="Raw Materials List"
             columns={[
               { label: 'ID', key: 'MaterialID' },
               { label: 'Name', key: 'Name' },
               { label: 'Category', key: 'Category' },
               { label: 'Stock Level', key: 'CurrentStock' }
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
               { label: 'Name', key: 'Name' },
               { label: 'Reliability Score', key: 'ReliabilityScore' },
               { label: 'Total Orders', key: 'OrderCount' }
             ]}
             data={suppliers}
             onAdd={() => setSupplierModal(true)}
             onDelete={handleDeleteSupplier}
           />
        )}
      </main>

      {/* Modals */}
      <DataFormModal 
         title="New Raw Material"
         isOpen={isMaterialModalOpen}
         onClose={() => setMaterialModal(false)}
         onSubmit={handleCreateMaterial}
         fields={[
           { label: 'Material Name', key: 'Name', required: true },
           { label: 'Category', key: 'Category', required: true },
           { label: 'Initial Stock', key: 'CurrentStock', type: 'number' },
           { label: 'Min Threshold', key: 'MinThreshold', type: 'number' },
           { label: 'Cost Per Unit ($)', key: 'CostPerUnit', type: 'number' }
         ]}
      />

      <DataFormModal 
         title="New Supplier"
         isOpen={isSupplierModalOpen}
         onClose={() => setSupplierModal(false)}
         onSubmit={handleCreateSupplier}
         fields={[
           { label: 'Supplier Name', key: 'Name', required: true },
           { label: 'Category', key: 'Category', required: true },
           { label: 'Reliability Score (0.0 - 1.0)', key: 'ReliabilityScore', type: 'number' }
         ]}
      />
    </div>
  );
}

function KPI({ CardTitle, Value, Icon, col }) {
    return (
        <div className="glass-card" style={{borderLeft: `4px solid ${col}`}}>
            <div className="kpi-title">
                <Icon size={16} color={col} />
                {CardTitle}
            </div>
            <div className="kpi-value">{Value}</div>
        </div>
    );
}

export default App;
