import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

/**
 * KPICard — Premium KPI card with status color, trend arrow, and sub-label.
 * Props:
 *  title      — string label
 *  value      — formatted display value (string)
 *  icon       — Lucide icon component
 *  color      — CSS color string (e.g. var(--accent-blue))
 *  trend      — 'up' | 'down' | 'neutral'
 *  trendGood  — boolean: is "up" good for this metric? (default true)
 *  subtitle   — optional sub-label
 *  status     — 'good' | 'warn' | 'danger' | null
 */
function KPICard({ title, value, icon: Icon, color, trend, trendGood = true, subtitle, status }) {
  const trendColor =
    trend === 'neutral' ? 'var(--text-muted)' :
    (trend === 'up') === trendGood ? 'var(--accent-green)' : 'var(--accent-red)';

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;

  const statusBorder =
    status === 'danger' ? 'var(--accent-red)' :
    status === 'warn'   ? 'var(--accent-amber)' :
    status === 'good'   ? 'var(--accent-green)' :
    color;

  const glowClass =
    status === 'danger' ? 'kpi-card--danger' :
    status === 'warn'   ? 'kpi-card--warn'   : '';

  return (
    <div className={`kpi-card ${glowClass}`} style={{ '--kpi-accent': statusBorder }}>
      <div className="kpi-card__header">
        <div className="kpi-card__icon" style={{ background: `color-mix(in srgb, ${color} 15%, transparent)` }}>
          <Icon size={18} color={color} />
        </div>
        {trend && (
          <div className="kpi-card__trend" style={{ color: trendColor }}>
            <TrendIcon size={14} />
          </div>
        )}
      </div>
      <div className="kpi-card__value">{value}</div>
      <div className="kpi-card__title">{title}</div>
      {subtitle && <div className="kpi-card__subtitle">{subtitle}</div>}
    </div>
  );
}

export default KPICard;
