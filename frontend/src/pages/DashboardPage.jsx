/**
 * Dashboard page — Analytics overview with charts.
 */
import { useState, useEffect } from 'react';
import { BarChart3, AlertTriangle, Loader2 } from 'lucide-react';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { getDashboard } from '../services/api';

const SEVERITY_COLORS = {
  Low: '#22c55e',
  Medium: '#eab308',
  High: '#f97316',
  Critical: '#ef4444',
};

const DAMAGE_COLORS = ['#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#6366f1'];

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await getDashboard();
      const data = response.data;
      if (data && data.total_analyses > 0) {
        setStats(data);
      } else {
        setStats(null);
      }
    } catch (err) {
      setError('Failed to load dashboard data. Please check if the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="page-center">
        <Loader2 size={40} className="spin" />
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-center">
        <AlertTriangle size={40} className="text-warning" />
        <p>{error}</p>
        <button className="btn btn--primary" onClick={loadDashboard}>
          Retry
        </button>
      </div>
    );
  }

  // No data yet
  if (!stats) {
    return (
      <div className="dashboard-page">
        <h1 className="page-title">Analytics Dashboard</h1>
        <p className="page-subtitle">
          Aggregate statistics from all road damage analyses.
        </p>
        <div className="card card--centered" style={{ padding: '4rem 2rem' }}>
          <BarChart3 size={56} className="text-muted" />
          <h3>No Analysis Data Yet</h3>
          <p className="text-muted">
            Dashboard statistics will appear here after you analyze road
            images or videos. Go to the <strong>Analyze</strong> page to get started.
          </p>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const severityData = Object.entries(stats.severity_distribution || {}).map(
    ([name, value]) => ({ name, value })
  );
  const damageTypeData = Object.entries(stats.damage_type_distribution || {}).map(
    ([name, value]) => ({ name, value })
  );
  const priorityData = Object.entries(stats.priority_distribution || {}).map(
    ([name, value]) => ({ name, value })
  );

  return (
    <div className="dashboard-page">
      <h1 className="page-title">Analytics Dashboard</h1>
      <p className="page-subtitle">
        Aggregate statistics from all road damage analyses.
      </p>

      {/* Stat Cards */}
      <div className="dashboard-stats">
        <div className="stat-card stat-card--highlight">
          <div className="stat-card__label">Total Analyses</div>
          <div className="stat-card__value">{stats.total_analyses}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Images Analyzed</div>
          <div className="stat-card__value">{stats.images_analyzed}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Videos Analyzed</div>
          <div className="stat-card__value">{stats.videos_analyzed}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Total Damages</div>
          <div className="stat-card__value">{stats.total_damages}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Potholes</div>
          <div className="stat-card__value">{stats.total_potholes}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Cracks</div>
          <div className="stat-card__value">{stats.total_cracks}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Avg Confidence</div>
          <div className="stat-card__value">
            {(stats.avg_confidence * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="charts-grid">
        {/* Severity Distribution */}
        {severityData.length > 0 && (
          <div className="chart-card">
            <h3>Severity Distribution</h3>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={severityData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                >
                  {severityData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={SEVERITY_COLORS[entry.name] || '#64748b'}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Damage Type Distribution */}
        {damageTypeData.length > 0 && (
          <div className="chart-card">
            <h3>Damage Types</h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={damageTypeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    background: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="value" name="Count">
                  {damageTypeData.map((_, idx) => (
                    <Cell key={idx} fill={DAMAGE_COLORS[idx % DAMAGE_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Priority Distribution */}
        {priorityData.length > 0 && (
          <div className="chart-card">
            <h3>Maintenance Priority</h3>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={priorityData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                >
                  {priorityData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={SEVERITY_COLORS[entry.name] || '#64748b'}
                    />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
