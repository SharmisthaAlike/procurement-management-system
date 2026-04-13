import React from 'react';
import { Trash2, Plus } from 'lucide-react';

export default function DataListView({ title, columns, data, onAdd, onDelete }) {
  return (
    <div className="animate-fade-in delay-1">
      <div className="list-header">
        <h1>{title}</h1>
        <button className="btn-primary" onClick={onAdd}>
          <Plus size={18} /> New
        </button>
      </div>

      <div className="glass-card table-container">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col, idx) => (
                <th key={idx}>{col.label}</th>
              ))}
              <th style={{ width: '80px', textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 1} style={{ textAlign: 'center', padding: '2rem' }}>
                  No records found.
                </td>
              </tr>
            ) : (
              data.map((row, rowIdx) => (
                <tr key={rowIdx}>
                  {columns.map((col, colIdx) => (
                    <td key={colIdx}>{row[col.key]}</td>
                  ))}
                  <td style={{ textAlign: 'center' }}>
                    <button className="btn-icon" onClick={() => onDelete(row)} title="Delete Record">
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
