import React, { useState, useRef, useCallback } from 'react';
import { Upload, FileText, CheckCircle, XCircle, Download, AlertCircle } from 'lucide-react';

const API_BASE = 'http://localhost:5001/api';

const TABLE_OPTIONS = [
  { value: 'PurchaseOrders', label: 'Purchase Orders', cols: 'SupplierID, MaterialID, OrderDate, ExpectedDeliveryDate, Quantity, TotalCost' },
  { value: 'Deliveries',     label: 'Deliveries',      cols: 'POID, ActualDeliveryDate, QuantityReceived, DefectQuantity' },
  { value: 'Suppliers',      label: 'Suppliers',        cols: 'Name, Category, ReliabilityScore' },
  { value: 'RawMaterials',   label: 'Raw Materials',    cols: 'Name, Category, CurrentStock, MinThreshold, CostPerUnit' },
];

function CSVUpload({ onSuccess }) {
  const [table, setTable] = useState('PurchaseOrders');
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [toast, setToast] = useState(null); // { type: 'success'|'error', message }
  const fileInputRef = useRef();

  const showToast = (type, message) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 5000);
  };

  const parseCSVPreview = (text) => {
    const lines = text.trim().split('\n').slice(0, 6);
    const rows = lines.map(l => l.split(',').map(c => c.trim().replace(/^"|"$/g, '')));
    return rows;
  };

  const handleFile = (f) => {
    if (!f || !f.name.endsWith('.csv')) {
      showToast('error', 'Please select a valid .csv file.');
      return;
    }
    setFile(f);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(parseCSVPreview(e.target.result));
    reader.readAsText(f);
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files[0];
    handleFile(f);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('table', table);
      const res = await fetch(`${API_BASE}/upload-csv`, { method: 'POST', body: formData });
      const data = await res.json();
      if (data.error) {
        showToast('error', data.error);
      } else {
        showToast('success', `✓ ${data.rows_inserted} rows inserted into ${data.table}`);
        setFile(null);
        setPreview(null);
        if (onSuccess) onSuccess();
      }
    } catch (e) {
      showToast('error', 'Upload failed. Is the backend running?');
    }
    setUploading(false);
  };

  const handleDownloadSample = async () => {
    const url = `${API_BASE}/sample-csv/${table}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = `sample_${table}.csv`;
    a.click();
  };

  const selectedTableInfo = TABLE_OPTIONS.find(t => t.value === table);

  return (
    <div className="csv-upload-container">
      {/* Toast */}
      {toast && (
        <div className={`toast toast--${toast.type}`}>
          {toast.type === 'success' ? <CheckCircle size={16} /> : <XCircle size={16} />}
          {toast.message}
        </div>
      )}

      <div className="upload-card">
        <div className="upload-card__header">
          <div className="upload-card__title-group">
            <Upload size={20} color="var(--accent-blue)" />
            <h2>Import CSV Data</h2>
          </div>
          <p className="upload-card__subtitle">
            Upload CSV files to populate the procurement database
          </p>
        </div>

        {/* Table Selector */}
        <div className="upload-field-group">
          <label className="upload-label">Target Table</label>
          <div className="table-selector">
            {TABLE_OPTIONS.map(opt => (
              <button
                key={opt.value}
                className={`table-btn ${table === opt.value ? 'table-btn--active' : ''}`}
                onClick={() => { setTable(opt.value); setFile(null); setPreview(null); }}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <p className="upload-cols-hint">
            <AlertCircle size={12} /> Required columns: <code>{selectedTableInfo.cols}</code>
          </p>
        </div>

        {/* Sample Download */}
        <button className="btn-download-sample" onClick={handleDownloadSample}>
          <Download size={14} /> Download Sample CSV for {selectedTableInfo.label}
        </button>

        {/* Drop Zone */}
        <div
          className={`drop-zone ${isDragging ? 'drop-zone--active' : ''} ${file ? 'drop-zone--filled' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            style={{ display: 'none' }}
            onChange={(e) => handleFile(e.target.files[0])}
          />
          {file ? (
            <div className="drop-zone__file-info">
              <FileText size={32} color="var(--accent-blue)" />
              <span className="drop-zone__filename">{file.name}</span>
              <span className="drop-zone__hint">Click to change file</span>
            </div>
          ) : (
            <div className="drop-zone__empty">
              <Upload size={32} color="var(--text-muted)" />
              <span>Drag & drop a CSV file here</span>
              <span className="drop-zone__hint">or click to browse</span>
            </div>
          )}
        </div>

        {/* Preview Table */}
        {preview && preview.length > 0 && (
          <div className="preview-section">
            <h3 className="preview-title">Preview (first 5 rows)</h3>
            <div className="table-container">
              <table className="data-table preview-table">
                <thead>
                  <tr>{preview[0].map((h, i) => <th key={i}>{h}</th>)}</tr>
                </thead>
                <tbody>
                  {preview.slice(1).map((row, ri) => (
                    <tr key={ri}>{row.map((cell, ci) => <td key={ci}>{cell}</td>)}</tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Upload Button */}
        <button
          className="btn-upload"
          onClick={handleUpload}
          disabled={!file || uploading}
        >
          {uploading ? (
            <span className="uploading-spinner" />
          ) : (
            <Upload size={16} />
          )}
          {uploading ? 'Uploading...' : `Upload to ${selectedTableInfo.label}`}
        </button>
      </div>
    </div>
  );
}

export default CSVUpload;
