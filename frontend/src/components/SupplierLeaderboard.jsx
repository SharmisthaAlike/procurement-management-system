import React from 'react';
import { Trophy, TrendingUp, Zap } from 'lucide-react';

export default function SupplierLeaderboard({ suppliers }) {
  if (!suppliers || suppliers.length === 0) {
    return (
      <div className="glass-card">
        <h2 className="chart-title">Supplier Reliability Leaderboard</h2>
        <p style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
          No supplier data available
        </p>
      </div>
    );
  }

  const getScoreBadgeColor = (score) => {
    if (score >= 80) return 'badge-excellent';
    if (score >= 70) return 'badge-good';
    if (score >= 60) return 'badge-fair';
    return 'badge-poor';
  };

  const getMedalIcon = (rank) => {
    if (rank === 0) return '🥇';
    if (rank === 1) return '🥈';
    if (rank === 2) return '🥉';
    return null;
  };

  return (
    <div className="glass-card leaderboard-card animate-fade-in delay-4">
      <div className="leaderboard-header">
        <h2 className="chart-title">
          <Trophy size={24} style={{ marginRight: '10px' }} />
          Supplier Reliability Leaderboard
        </h2>
        <span className="ml-badge">Score-Based Ranking</span>
      </div>

      <div className="leaderboard-table">
        <div className="leaderboard-row header-row">
          <div className="col-rank">Rank</div>
          <div className="col-name">Supplier</div>
          <div className="col-score">Reliability Score</div>
          <div className="col-metrics">OTIF</div>
          <div className="col-metrics">Lead Time</div>
          <div className="col-metrics">Defects</div>
          <div className="col-metrics">Orders</div>
        </div>

        {suppliers.map((supplier, index) => (
          <div key={supplier.supplier_id} className={`leaderboard-row ${index < 3 ? 'top-rank' : ''}`}>
            <div className="col-rank">
              <div className="rank-badge">
                {getMedalIcon(index) || `#${index + 1}`}
              </div>
            </div>
            <div className="col-name">
              <div className="supplier-name">{supplier.name}</div>
              <div className="supplier-category">{supplier.category}</div>
            </div>
            <div className="col-score">
              <div className={`score-badge ${getScoreBadgeColor(supplier.reliability_score)}`}>
                {supplier.reliability_score.toFixed(1)}
              </div>
            </div>
            <div className="col-metrics">
              <span className="metric-value">{supplier.otif.toFixed(0)}%</span>
            </div>
            <div className="col-metrics">
              <span className="metric-value">{supplier.avg_lead_time_days.toFixed(0)}d</span>
            </div>
            <div className="col-metrics">
              <span className="metric-value">{supplier.defect_rate.toFixed(1)}%</span>
            </div>
            <div className="col-metrics">
              <span className="metric-value">{supplier.total_orders}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="leaderboard-footer">
        <p>
          <Zap size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          Scores calculated using: 40% OTIF + 30% Lead Time + 20% Quality + 10% Cost
        </p>
      </div>
    </div>
  );
}
