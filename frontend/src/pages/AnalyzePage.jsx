/**
 * Analysis page — Image, Video, and Live camera input tabs.
 */
import { useState, useRef, useCallback, useEffect } from 'react';
import {
  Upload,
  Image,
  Video,
  Camera,
  X,
  Loader2,
  AlertCircle,
  Download,
  VideoOff,
  Scan,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';
import { analyzeImage, analyzeVideo, getOutputUrl, getReportUrl } from '../services/api';

const TABS = [
  { id: 'image', label: 'Image Analysis', icon: Image },
  { id: 'video', label: 'Video Analysis', icon: Video },
  { id: 'live', label: 'Live Detection', icon: Camera },
];

const DEMO_SAMPLES = [
  {
    id: 'pothole',
    name: 'Severe Pothole',
    desc: 'Deep asphalt cavity with water accumulation',
    path: '/samples/pothole_sample.jpg',
    tag: 'Pothole'
  },
  {
    id: 'cracks',
    name: 'Longitudinal & Transverse Cracks',
    desc: 'Extensive surface fracture network',
    path: '/samples/cracks_sample.jpg',
    tag: 'Cracks'
  },
  {
    id: 'clean',
    name: 'Good Condition Road',
    desc: 'Newly resurfaced asphalt with crisp lane marks',
    path: '/samples/clean_road_sample.jpg',
    tag: 'No Damage'
  }
];

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
    Moderate: 'badge--yellow',
    Urgent: 'badge--red',
  };
  return (
    <span className={`badge ${colors[label] || 'badge--gray'}`}>
      {label} ({score}/100)
    </span>
  );
}

export default function AnalyzePage() {
  const [activeTab, setActiveTab] = useState('image');
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Live Camera states
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraLoading, setCameraLoading] = useState(false);
  const [continuousScan, setContinuousScan] = useState(false);

  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const scanIntervalRef = useRef(null);

  const acceptTypes = activeTab === 'image'
    ? '.jpg,.jpeg,.png'
    : '.mp4,.mov,.avi';

  // Stop camera stream cleanly
  const stopCamera = useCallback(() => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
    setContinuousScan(false);
  }, []);

  const resetState = useCallback(() => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    setProgress(0);
    stopCamera();
  }, [stopCamera]);

  useEffect(() => {
    return () => stopCamera();
  }, [stopCamera]);

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    resetState();
  };

  const handleFile = useCallback((selectedFile) => {
    setError(null);
    setResult(null);
    setProgress(0);

    const ext = '.' + selectedFile.name.split('.').pop().toLowerCase();
    const allowed = activeTab === 'image'
      ? ['.jpg', '.jpeg', '.png']
      : ['.mp4', '.mov', '.avi'];

    if (!allowed.includes(ext)) {
      setError(`Unsupported file format "${ext}". Allowed: ${allowed.join(', ')}`);
      return;
    }

    if (selectedFile.size > 100 * 1024 * 1024) {
      setError('File too large. Maximum allowed: 100MB');
      return;
    }

    setFile(selectedFile);

    if (activeTab === 'image') {
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target.result);
      reader.readAsDataURL(selectedFile);
    } else {
      setPreview(URL.createObjectURL(selectedFile));
    }
  }, [activeTab]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) handleFile(droppedFile);
  }, [handleFile]);

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setProgress(0);

    try {
      const onProgress = (progressEvent) => {
        if (progressEvent.total) {
          const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(pct);
        }
      };

      const response = activeTab === 'image'
        ? await analyzeImage(file, onProgress)
        : await analyzeVideo(file, onProgress);

      setResult(response.data);
    } catch (err) {
      const msg = err.response?.data?.detail
        || err.response?.data?.message
        || 'Analysis failed. Please check if the backend is running.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  // Start Webcam
  const startCamera = async () => {
    setError(null);
    setCameraLoading(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setCameraActive(true);
    } catch (err) {
      setError('Camera access denied or unavailable: ' + err.message);
    } finally {
      setCameraLoading(false);
    }
  };

  // Capture frame from webcam and run inference
  const captureAndAnalyze = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(async (blob) => {
      if (!blob) return;
      const capturedFile = new File([blob], `live_frame_${Date.now()}.jpg`, { type: 'image/jpeg' });
      setPreview(canvas.toDataURL('image/jpeg'));
      setLoading(true);
      setError(null);

      try {
        const res = await analyzeImage(capturedFile);
        setResult(res.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Live frame analysis failed.');
      } finally {
        setLoading(false);
      }
    }, 'image/jpeg', 0.92);
  };

  // Toggle continuous scan every 3.5s
  const toggleContinuousScan = () => {
    if (continuousScan) {
      if (scanIntervalRef.current) clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
      setContinuousScan(false);
    } else {
      setContinuousScan(true);
      captureAndAnalyze();
      scanIntervalRef.current = setInterval(() => {
        captureAndAnalyze();
      }, 3500);
    }
  };

  // Load demo sample image
  const loadDemoSample = async (sample) => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);
      const res = await fetch(sample.path);
      const blob = await res.blob();
      const sampleFile = new File([blob], `${sample.id}_sample.jpg`, { type: 'image/jpeg' });
      setFile(sampleFile);
      setPreview(sample.path);
    } catch (err) {
      setError('Could not load demo image: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="analyze-page">
      <h1 className="page-title">Road Damage Analysis</h1>
      <p className="page-subtitle">
        Upload road images, dashcam videos, or use live camera detection to detect and prioritize road repairs.
      </p>

      {/* Tabs */}
      <div className="tabs">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={`tab ${activeTab === id ? 'tab--active' : ''}`}
            onClick={() => handleTabChange(id)}
          >
            <Icon size={18} />
            {label}
          </button>
        ))}
      </div>

      {/* Demo Samples Gallery (Images tab only) */}
      {activeTab === 'image' && (
        <div className="demo-samples-bar card mb-6" style={{ background: 'var(--navy-900)', border: '1px solid var(--navy-800)', padding: '1rem 1.25rem' }}>
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm font-semibold text-muted uppercase tracking-wider">
              Quick Test Demo Imagery (Click to load)
            </span>
            <span className="text-xs text-muted">Ready-to-analyze asphalt captures</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
            {DEMO_SAMPLES.map((sample) => (
              <div
                key={sample.id}
                onClick={() => loadDemoSample(sample)}
                className="sample-card flex items-center gap-3 p-2 rounded cursor-pointer transition"
                style={{
                  background: 'var(--navy-800)',
                  border: '1px solid var(--navy-700)',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  cursor: 'pointer'
                }}
              >
                <img
                  src={sample.path}
                  alt={sample.name}
                  style={{ width: '48px', height: '48px', objectFit: 'cover', borderRadius: '4px' }}
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold">{sample.name}</span>
                    <span className="badge badge--sm badge--gray">{sample.tag}</span>
                  </div>
                  <p className="text-muted text-xs truncate" style={{ margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {sample.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Live Camera Tab */}
      {activeTab === 'live' ? (
        <div className="live-camera-section card">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3>Live Camera Feed</h3>
              <p className="text-muted text-sm">
                Stream real-time dashcam or mobile camera video to detect road damage on-the-fly.
              </p>
            </div>
            <div className="flex gap-2">
              {!cameraActive ? (
                <button
                  className="btn btn--primary btn--sm"
                  onClick={startCamera}
                  disabled={cameraLoading}
                >
                  <Camera size={16} />
                  {cameraLoading ? 'Starting Camera...' : 'Start Camera'}
                </button>
              ) : (
                <>
                  <button
                    className="btn btn--outline btn--sm"
                    onClick={captureAndAnalyze}
                    disabled={loading}
                  >
                    <Scan size={16} />
                    {loading ? 'Analyzing...' : 'Analyze Current Frame'}
                  </button>
                  <button
                    className={`btn btn--sm ${continuousScan ? 'btn--accent' : 'btn--outline'}`}
                    onClick={toggleContinuousScan}
                  >
                    <RefreshCw size={16} className={continuousScan ? 'spin' : ''} />
                    {continuousScan ? 'Auto-Scanning (ON)' : 'Continuous Auto-Scan'}
                  </button>
                  <button
                    className="btn btn--danger btn--sm"
                    onClick={stopCamera}
                  >
                    <VideoOff size={16} />
                    Stop Camera
                  </button>
                </>
              )}
            </div>
          </div>

          {error && (
            <div className="alert alert--error mb-4">
              <AlertCircle size={18} />
              {error}
            </div>
          )}

          {/* Camera Viewport */}
          <div className="camera-viewport relative" style={{ minHeight: '380px', background: '#0a0e1a', borderRadius: '8px', overflow: 'hidden', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <video
              ref={videoRef}
              style={{ width: '100%', maxHeight: '480px', objectFit: 'contain', display: cameraActive ? 'block' : 'none' }}
              muted
              playsInline
            />
            <canvas ref={canvasRef} style={{ display: 'none' }} />

            {!cameraActive && (
              <div className="text-center p-6">
                <Camera size={56} className="text-muted mb-3" style={{ margin: '0 auto 12px auto' }} />
                <h4>Camera Inactive</h4>
                <p className="text-muted text-sm max-w-md">
                  Click <strong>Start Camera</strong> to initialize your webcam or mobile video stream for road inspection.
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Image / Video Upload Area */
        <div className="analyze-content">
          <div className="upload-section">
            <div
              className={`dropzone ${dragOver ? 'dropzone--active' : ''} ${file ? 'dropzone--has-file' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => !file && fileInputRef.current?.click()}
            >
              {file ? (
                <div className="dropzone__preview">
                  {activeTab === 'image' ? (
                    <img src={preview} alt="Preview" className="dropzone__image" />
                  ) : (
                    <video src={preview} className="dropzone__video" controls />
                  )}
                  <div className="dropzone__file-info">
                    <span>{file.name}</span>
                    <span className="text-muted">
                      {(file.size / (1024 * 1024)).toFixed(1)} MB
                    </span>
                  </div>
                  <button
                    className="dropzone__remove"
                    onClick={(e) => { e.stopPropagation(); resetState(); }}
                  >
                    <X size={18} />
                  </button>
                </div>
              ) : (
                <div className="dropzone__empty">
                  <Upload size={40} />
                  <p>
                    Drag & drop a road {activeTab} here, or click to browse
                  </p>
                  <span className="text-muted">
                    Supported: {activeTab === 'image' ? 'JPG, JPEG, PNG' : 'MP4, MOV, AVI'}
                    {' '}• Max 100MB
                  </span>
                </div>
              )}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept={acceptTypes}
              onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
              style={{ display: 'none' }}
            />

            {error && (
              <div className="alert alert--error">
                <AlertCircle size={18} />
                {error}
              </div>
            )}

            <button
              className="btn btn--primary btn--full"
              onClick={handleAnalyze}
              disabled={!file || loading}
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="spin" />
                  Analyzing{progress > 0 ? ` (${progress}%)` : '...'}
                </>
              ) : (
                <>
                  <Camera size={18} />
                  Analyze {activeTab === 'image' ? 'Image' : 'Video'}
                </>
              )}
            </button>

            {loading && (
              <div className="progress-bar">
                <div
                  className="progress-bar__fill"
                  style={{ width: `${progress}%` }}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Results Section (Common to Image, Video, and Live) */}
      {result && (
        <div className="results-section mt-8">
          <div className="flex justify-between items-center mb-4">
            <h2>Inspection Results</h2>
            <a
              href={getReportUrl(result.analysis_id)}
              target="_blank"
              rel="noreferrer"
              className="btn btn--outline btn--sm"
            >
              <Download size={16} />
              Export PDF Inspection Report
            </a>
          </div>

          {/* Video Results Player */}
          {result.output_video_url && (
            <div className="comparison mb-6">
              <div className="comparison__panel" style={{ width: '100%' }}>
                <h3>Annotated Road Video Inspection</h3>
                <video
                  src={getOutputUrl(result.output_video_url)}
                  controls
                  autoPlay
                  muted
                  loop
                  style={{ width: '100%', borderRadius: '8px', border: '1px solid var(--color-border)' }}
                />
              </div>
            </div>
          )}

          {/* Side-by-side comparison (images) */}
          {result.output_image_url && (
            <div className="comparison mb-6">
              <div className="comparison__panel">
                <h3>Original Capture</h3>
                <img src={preview} alt="Original" />
              </div>
              <div className="comparison__panel">
                <h3>Annotated Detections</h3>
                <img
                  src={getOutputUrl(result.output_image_url)}
                  alt="Detected"
                />
              </div>
            </div>
          )}

          {/* Summary Cards */}
          <div className="result-summary">
            <div className="stat-card">
              <div className="stat-card__label">Total Damage</div>
              <div className="stat-card__value">{result.damage_count}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card__label">Potholes</div>
              <div className="stat-card__value">{result.pothole_count}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card__label">Cracks</div>
              <div className="stat-card__value">{result.crack_count}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card__label">Avg Confidence</div>
              <div className="stat-card__value">
                {(result.avg_confidence * 100).toFixed(0)}%
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-card__label">Highest Severity</div>
              <div className="stat-card__value">
                <SeverityBadge severity={result.highest_severity} />
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-card__label">Priority Score</div>
              <div className="stat-card__value">
                <PriorityBadge
                  label={result.priority_label}
                  score={result.priority_score}
                />
              </div>
            </div>
          </div>

          {/* Recommendation */}
          {result.recommendation && (
            <div className="recommendation-card mb-6">
              <h3>Maintenance Engineering Recommendation</h3>
              <p>{result.recommendation}</p>
              <small className="text-muted">
                This is an automated AI-based decision-support prototype.
                Final road-maintenance decisions should be verified through
                professional on-site inspection.
              </small>
            </div>
          )}

          {/* Detections Table */}
          {result.detections && result.detections.length > 0 ? (
            <div className="card">
              <h3>Detection Details ({result.detections.length})</h3>
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Defect Type</th>
                      <th>Confidence</th>
                      <th>Severity</th>
                      <th>Area Ratio</th>
                      <th>Coordinates [x1, y1, x2, y2]</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.detections.map((det, idx) => (
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
              <h3>No Road Damage Detected</h3>
              <p className="text-muted">
                No road damage was detected above the confidence threshold. The inspected road surface is in acceptable operating condition.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
