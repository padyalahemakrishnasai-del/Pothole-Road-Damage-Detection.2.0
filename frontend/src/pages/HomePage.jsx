import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Shield, Camera, BarChart3, AlertTriangle, Zap, CheckCircle, Cpu, Activity } from 'lucide-react';
import { checkHealth, getModelInfo } from '../services/api';

const FEATURES = [
  {
    icon: Camera,
    title: 'Image & Video Analysis',
    description: 'Upload road images or videos for instant AI-powered damage detection.',
  },
  {
    icon: AlertTriangle,
    title: 'Damage Classification',
    description: 'Identify potholes, cracks, and surface deterioration with bounding boxes.',
  },
  {
    icon: Zap,
    title: 'Severity Estimation',
    description: 'Heuristic severity levels from Low to Critical based on damage characteristics.',
  },
  {
    icon: BarChart3,
    title: 'Priority Scoring',
    description: 'Transparent maintenance priority scores to help triage repair needs.',
  },
  {
    icon: CheckCircle,
    title: 'Inspection Reports',
    description: 'Generate downloadable reports for each analysis with full details.',
  },
  {
    icon: Shield,
    title: 'Decision Support',
    description: 'AI-based prototype to assist authorities in road maintenance planning.',
  },
];

export default function HomePage() {
  const [health, setHealth] = useState({ online: false, device: 'unknown' });
  const [modelInfo, setModelInfo] = useState(null);

  useEffect(() => {
    checkHealth()
      .then(res => setHealth({ online: true, device: res.data.device }))
      .catch(() => setHealth({ online: false, device: 'offline' }));

    getModelInfo()
      .then(res => setModelInfo(res.data))
      .catch(() => setModelInfo(null));
  }, []);

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero__badge flex items-center gap-2">
          <span className={`inline-block w-2 h-2 rounded-full ${health.online ? 'bg-green-400' : 'bg-red-400'}`} style={{ width: 8, height: 8, borderRadius: '50%', background: health.online ? '#22c55e' : '#ef4444' }} />
          <span>{health.online ? 'System Online' : 'Connecting to Server...'}</span>
          {modelInfo && (
            <>
              <span className="text-muted">•</span>
              <span>Model: {modelInfo.model_name}</span>
              <span className="text-muted">•</span>
              <span className="uppercase text-xs font-mono">{health.device}</span>
            </>
          )}
        </div>
        <h1 className="hero__title">
          <span className="hero__title-accent">AI RoadGuard</span>
        </h1>
        <p className="hero__subtitle">
          Road Damage Detection & Maintenance Prioritization
        </p>
        <p className="hero__description">
          Detect potholes, cracks, and surface deterioration from road imagery
          using computer vision. Estimate severity and prioritize maintenance
          needs with transparent, AI-driven decision support.
        </p>
        <div className="hero__actions">
          <Link to="/analyze" className="btn btn--primary btn--lg">
            <Camera size={20} />
            Analyze Road
          </Link>
          <Link to="/dashboard" className="btn btn--outline btn--lg">
            <BarChart3 size={20} />
            View Dashboard
          </Link>
        </div>

        {/* Decorative road lines */}
        <div className="hero__road-decoration">
          <div className="hero__road-line" />
          <div className="hero__road-line hero__road-line--dashed" />
          <div className="hero__road-line" />
        </div>
      </section>

      {/* Features Grid */}
      <section className="features-section">
        <h2 className="section-title">System Capabilities</h2>
        <p className="section-subtitle">
          An end-to-end AI/ML pipeline for road damage detection and maintenance planning.
        </p>
        <div className="features-grid">
          {FEATURES.map((feature, idx) => (
            <div key={idx} className="feature-card">
              <div className="feature-card__icon">
                <feature.icon size={24} />
              </div>
              <h3 className="feature-card__title">{feature.title}</h3>
              <p className="feature-card__description">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pipeline Overview */}
      <section className="pipeline-section">
        <h2 className="section-title">Detection Pipeline</h2>
        <div className="pipeline">
          {[
            'Upload Image / Video',
            'Preprocessing',
            'YOLO Object Detection',
            'Damage Classification',
            'Severity Estimation',
            'Priority Scoring',
            'Report & Dashboard',
          ].map((step, idx) => (
            <div key={idx} className="pipeline__step">
              <div className="pipeline__step-number">{idx + 1}</div>
              <div className="pipeline__step-label">{step}</div>
              {idx < 6 && <div className="pipeline__connector" />}
            </div>
          ))}
        </div>
      </section>

      {/* Disclaimer */}
      <section className="disclaimer-section">
        <div className="disclaimer">
          <AlertTriangle size={18} />
          <p>
            This system is an AI-based decision-support prototype. Final
            road-maintenance decisions should be verified through professional
            engineering inspection.
          </p>
        </div>
      </section>
    </div>
  );
}
