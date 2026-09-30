import { useState, useEffect } from 'react';
import { Clock, Loader2, AlertTriangle, ExternalLink, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getHistory, deleteAnalysis } from '../services/api';

function SeverityBadge({ severity }) {
  const colors = {
    Minor: 'badge--green',
    Moderate: 'badge--yellow',
    Severe: 'badge--red',
    Low: 'badge--green',
    Medium: 'badge--yellow',
    High: 'badge--orange',
    Critical: 'badge--red',
    None: 'badge--gray',
  };
  return (
    <span className={`badge badge--sm ${colors[severity] || 'badge--gray'}`}>
      {severity}
    </span>
  );
}

export default function HistoryPage() {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const response = await getHistory();
      const list = Array.isArray(response.data) ? response.data : (response.data.analyses || []);
      setAnalyses(list);
    } catch (err) {
      setError('Failed to load analysis history. Please check if the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this analysis record?')) return;
    try {
      await deleteAnalysis(id);
      setAnalyses(prev => prev.filter(a => a.analysis_id !== id));
    } catch (err) {
      alert('Failed to delete: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) {
    return (
      <div className="page-center">
        <Loader2 size={40} className="spin" />
        <p>Loading history...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-center">
        <AlertTriangle size={40} className="text-warning" />
        <p>{error}</p>
        <button className="btn btn--primary" onClick={loadHistory}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="history-page">
      <h1 className="page-title">Analysis History</h1>
      <p className="page-subtitle">
        Review past road damage analyses and their results.
      </p>

      {analyses.length === 0 ? (
        <div className="card card--centered" style={{ padding: '4rem 2rem' }}>
          <Clock size={56} className="text-muted" />
          <h3>No Analysis History</h3>
          <p className="text-muted">
            Your analysis history will appear here after you analyze road
            images or videos. Go to the <strong>Analyze</strong> page to get started.
          </p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Analysis ID</th>
                <th>Date/Time</th>
                <th>File Name</th>
                <th>Type</th>
                <th>Damages</th>
                <th>Severity</th>
                <th>Priority</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {analyses.map((a) => (
                <tr key={a.analysis_id}>
                  <td className="font-mono text-sm">
                    {a.analysis_id.slice(0, 8)}...
                  </td>
                  <td>{new Date(a.created_at).toLocaleString()}</td>
                  <td>{a.file_name}</td>
                  <td>
                    <span className="badge badge--sm badge--blue">
                      {a.file_type}
                    </span>
                  </td>
                  <td>{a.damage_count}</td>
                  <td><SeverityBadge severity={a.highest_severity} /></td>
                  <td>{a.priority_score}/100</td>
                  <td>
                    <span className={`badge badge--sm ${
                      a.status === 'completed' ? 'badge--green' : 'badge--red'
                    }`}>
                      {a.status}
                    </span>
                  </td>
                  <td className="flex items-center gap-2">
                    <Link
                      to={`/analysis/${a.analysis_id}`}
                      className="btn btn--sm btn--outline"
                    >
                      <ExternalLink size={14} />
                      View
                    </Link>
                    <button
                      className="btn btn--sm btn--outline text-danger"
                      onClick={(e) => handleDelete(a.analysis_id, e)}
                      title="Delete Analysis"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
