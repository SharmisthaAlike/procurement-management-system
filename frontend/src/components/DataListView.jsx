import React, { useState } from 'react';
import { Plus, Trash2, Search } from 'lucide-react';

function DataListView({ title, columns, data, onAdd, onDelete }) {
  const [search, setSearch] = useState('');

  const filtered = data.filter(row =>
    columns.some(col =>
      String(row[col.key] ?? '').toLowerCase().includes(search.toLowerCase())
    )
  );

  return (
    <div className="dashboard-container">
      <div className="list-header animate-fade-in delay-1">
        <div>
          <h1>{title}</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '0.25rem', fontSize: '0.9rem' }}>
            {filtered.length} record{filtered.length !== 1 ? 's' : ''} found
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div className="search-box">
            <Search size={14} color="var(--text-muted)" />
            <input
              className="search-input"
              placeholder="Search..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <button className="btn-primary" onClick={onAdd}>
            <Plus size={16} /> Add New
          </button>
        </div>
      </div>

      <div className="glass-card animate-fade-in delay-2">
        <div className="table-container">
          {filtered.length === 0 ? (
            <div className="empty-state">
              <p>No records found{search ? ` for "${search}"` : ''}.</p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  {columns.map(col => <th key={col.key}>{col.label}</th>)}
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row, idx) => (
                  <tr key={idx}>
                    {columns.map(col => (
                      <td key={col.key}>
                        {col.render ? col.render(row[col.key], row) : (row[col.key] ?? '—')}
                      </td>
                    ))}
                    <td>
                      <button className="btn-icon" onClick={() => onDelete(row)} title="Delete">
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

export default DataListView;
