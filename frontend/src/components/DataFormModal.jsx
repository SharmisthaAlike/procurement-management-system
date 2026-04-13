import React, { useState } from 'react';
import { X } from 'lucide-react';

export default function DataFormModal({ title, fields, isOpen, onClose, onSubmit }) {
  const [formData, setFormData] = useState({});

  if (!isOpen) return null;

  const handleChange = (e, key) => {
    setFormData({ ...formData, [key]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
    setFormData({}); // reset on submit
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content animate-fade-in">
        <div className="modal-header">
          <h2 style={{ fontSize: '1.25rem' }}>{title}</h2>
          <button className="btn-icon" onClick={onClose}><X size={20} /></button>
        </div>
        
        <form className="modal-body" onSubmit={handleSubmit}>
          {fields.map((field, idx) => (
            <div className="form-group" key={idx}>
              <label>{field.label}</label>
              <input 
                type={field.type || "text"}
                className="form-input"
                name={field.key}
                required={field.required}
                value={formData[field.key] || ''}
                onChange={(e) => handleChange(e, field.key)}
                placeholder={field.placeholder || ''}
              />
            </div>
          ))}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
            <button type="submit" className="btn-primary">Save Document</button>
          </div>
        </form>
      </div>
    </div>
  );
}
