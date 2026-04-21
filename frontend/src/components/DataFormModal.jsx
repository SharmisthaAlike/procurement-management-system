import React, { useState } from 'react';
import { X, Save } from 'lucide-react';

export default function DataFormModal({ title, fields, isOpen, onClose, onSubmit }) {
  const [formData, setFormData] = useState({});

  if (!isOpen) return null;

  const handleChange = (e, key) => {
    setFormData({ ...formData, [key]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
    setFormData({});
  };

  return (
    <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal-content animate-fade-in">
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="btn-icon" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>

        <form className="modal-body" onSubmit={handleSubmit}>
          {fields.map((field, idx) => (
            <div className="form-group" key={idx}>
              <label>{field.label}{field.required && <span style={{ color: 'var(--accent-red)', marginLeft: '0.25rem' }}>*</span>}</label>
              <input
                type={field.type || 'text'}
                className="form-input"
                name={field.key}
                required={field.required}
                value={formData[field.key] || ''}
                onChange={(e) => handleChange(e, field.key)}
                placeholder={field.placeholder || ''}
                step={field.type === 'number' ? 'any' : undefined}
              />
            </div>
          ))}
          <div className="modal-footer">
            <button type="button" className="btn-cancel" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-primary"><Save size={15} /> Save Record</button>
          </div>
        </form>
      </div>
    </div>
  );
}
