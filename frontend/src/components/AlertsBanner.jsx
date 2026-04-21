import React from 'react';
import { AlertTriangle, AlertCircle, Clock } from 'lucide-react';

export default function AlertsBanner({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return null;
  }

  const getAlertIcon = (type) => {
    switch(type) {
      case 'LOW_RELIABILITY':
        return <AlertTriangle size={20} />;
      case 'HIGH_DELAY_RISK':
        return <Clock size={20} />;
      case 'LOW_STOCK':
        return <AlertCircle size={20} />;
      default:
        return <AlertTriangle size={20} />;
    }
  };

  const getAlertStyle = (severity) => {
    switch(severity) {
      case 'HIGH':
        return 'alert-high';
      case 'MEDIUM':
        return 'alert-medium';
      default:
        return 'alert-low';
    }
  };

  return (
    <div className="alerts-container">
      {alerts.map((alert, idx) => (
        <div key={idx} className={`alert-item ${getAlertStyle(alert.severity)}`}>
          <div className="alert-icon">
            {getAlertIcon(alert.type)}
          </div>
          <div className="alert-content">
            <div className="alert-title">{alert.message}</div>
            <div className="alert-details">{alert.details}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
