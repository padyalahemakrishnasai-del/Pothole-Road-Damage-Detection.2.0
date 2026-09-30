/**
 * Analysis Detail Page — Deep inspection of a single historical analysis.
 */
import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  FileText,
  AlertTriangle,
  Loader2,
  Trash2,
  CheckCircle2,
  ShieldAlert,
  Download
} from 'lucide-react';
import { getAnalysis, deleteAnalysis, getOutputUrl, getReportUrl } from '../services/api';

function SeverityBadge({ severity }) {
  const colors = {
    Minor: 'badge--green',
    Moderate: 'badge--yellow',
    Severe: 'badge--red',
    None: 'badge--gray',
  };
  return (
    <span className={`badge ${colors[severity] || 'badge--gray'}`}>
      {severity}
    </span>
  );
}

function PriorityBadge({ label, score }) {
  const colors = {
    Low: 'badge--green',
    Medium: 'badge--yellow',
    High: 'badge--orange',
    Critical: 'badge--red',
  };
  return (
    <span className={`badge ${colors[label] || 'badge--gray'}`}>
      {label} ({score}/100)
    </span>
  );
}

export default function AnalysisDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await getAnalysis(id);
      setAnalysis(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load analysis details.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this analysis record?')) return;
    try {
      setDeleting(true);
      await deleteAnalysis(id);
      navigate('/history');
    } catch (err) {
      alert('Failed to delete analysis: ' + (err.response?.data?.detail || err.message));
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="page-center">
        <Loader2 size={40} className="spin" />
        <p>Loading analysis details...</p>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="page-center">
        <AlertTriangle size={40} className="text-warning" />
        <p>{error || 'Analysis record not found.'}</p>
        <Link to="/history" className="btn btn--primary">
          <ArrowLeft size={16} /> Return to History
        </Link>
      </div>
    );
  }

  return (
    <div className="analysis-detail-page">
      <div className="page-header flex justify-between items-center mb-6">
        <div>
          <Link to="/history" className="btn btn--outline btn--sm mb-2">
            <ArrowLeft size={14} /> Back to History
          </Link>
          <h1 className="page-title">{analysis.file_name}</h1>
          <p className="page-subtitle flex items-center gap-3">
            <span>ID: <code className="font-mono">{analysis.analysis_id}</code></span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Calendar size={14} /> {new Date(analysis.created_at).toLocaleString()}
            </span>
          </p>
        </div>

        <div className="flex gap-2">
          <a
            href={getReportUrl(analysis.analysis_id)}
            target="_blank"
            rel="noreferrer"
            className="btn btn--outline btn--sm"
          >
            <Download size={16} />
            Export PDF Report
          </a>
          <button
            className="btn btn--danger btn--sm"
            onClick={handleDelete}
            disabled={deleting}
          >
            <Trash2 size={16} />
            {deleting ? 'Deleting...' : 'Delete Record'}
          </button>
        </div>
      </div>

      {/* Main Analysis Display */}
      <div className="results-section">
        {analysis.output_video_url && (
          <div className="comparison mb-6">
            <div className="comparison__panel" style={{ width: '100%' }}>
              <h3>Annotated Road Video Inspection</h3>
              <video
                src={getOutputUrl(analysis.output_video_url)}
                controls
                autoPlay
                muted
                loop
                style={{ width: '100%', borderRadius: '8px', border: '1px solid var(--color-border)' }}
              />
            </div>
          </div>
        )}

        {analysis.output_image_url && (
          <div className="comparison mb-6">
            <div className="comparison__panel">
              <h3>Annotated Road Inspection Frame</h3>
              <img
                src={getOutputUrl(analysis.output_image_url)}
                alt="Detected Damage"
                style={{ width: '100%', borderRadius: '8px', border: '1px solid var(--color-border)' }}
              />
            </div>
          </div>
        )}

        {/* Summary Cards */}
        <div className="result-summary">
          <div className="stat-card">
            <div className="stat-card__label">Total Damage</div>
            <div className="stat-card__value">{analysis.damage_count}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card__label">Potholes</div>
            <div className="stat-card__value">{analysis.pothole_count}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card__label">Cracks</div>
            <div className="stat-card__value">{analysis.crack_count}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card__label">Avg Confidence</div>
            <div className="stat-card__value">
              {(analysis.avg_confidence * 100).toFixed(0)}%
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card__label">Highest Severity</div>
            <div className="stat-card__value">
              <SeverityBadge severity={analysis.highest_severity} />
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card__label">Priority Score</div>
            <div className="stat-card__value">
              <PriorityBadge
                label={analysis.priority_label}
                score={analysis.priority_score}
              />
            </div>
          </div>
        </div>

        {/* Recommendation Box */}
        {analysis.recommendation && (
          <div className="recommendation-card mb-6">
            <div className="flex items-center gap-2 mb-2">
              <ShieldAlert size={20} className="text-accent" />
              <h3 style={{ margin: 0 }}>Maintenance Engineering Recommendation</h3>
            </div>
            <p style={{ fontSize: '1.05rem', lineHeight: '1.6' }}>{analysis.recommendation}</p>
            <small className="text-muted">
              Prototype recommendation formulated via algorithmic defect density and structural hazard multipliers.
            </small>
          </div>
        )}

        {/* Detections Breakdown Table */}
        {analysis.detections && analysis.detections.length > 0 ? (
          <div className="card">
            <h3>Detected Damage Instances ({analysis.detections.length})</h3>
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Defect Category</th>
                    <th>Confidence</th>
                    <th>Estimated Severity</th>
                    <th>Bounding Box Area</th>
                    <th>Coordinates [x1, y1, x2, y2]</th>
                  </tr>
                </thead>
                <tbody>
                  {analysis.detections.map((det, idx) => (
                    <tr key={idx}>
                      <td>{idx + 1}</td>
                      <td className="font-semibold">{det.class_name}</td>
                      <td>{(det.confidence * 100).toFixed(1)}%</td>
                      <td><SeverityBadge severity={det.severity} /></td>
                      <td>{(det.area_ratio * 100).toFixed(2)}%</td>
                      <td className="font-mono text-xs text-muted">
                        [{det.bbox.join(', ')}]
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="card card--centered">
            <CheckCircle2 size={40} className="text-green-500" />
            <h3>No Road Defects Detected</h3>
            <p className="text-muted">
              The road surface inspected in this file met baseline quality standards with no detected potholes or cracks.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
