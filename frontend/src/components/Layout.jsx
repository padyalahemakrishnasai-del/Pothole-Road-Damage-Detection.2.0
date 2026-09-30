/**
 * Main application layout with sidebar navigation.
 */
import { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import {
  Home,
  Camera,
  BarChart3,
  Clock,
  Settings,
  Menu,
  X,
  Shield,
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/analyze', label: 'Analyze', icon: Camera },
  { path: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { path: '/history', label: 'History', icon: Clock },
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="app-layout">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'sidebar--open' : ''}`}>
        <div className="sidebar__header">
          <Link to="/" className="sidebar__logo" onClick={() => setSidebarOpen(false)}>
            <Shield className="sidebar__logo-icon" />
            <div>
              <span className="sidebar__logo-title">AI RoadGuard</span>
              <span className="sidebar__logo-subtitle">Road Damage Detection</span>
            </div>
          </Link>
          <button
            className="sidebar__close"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar__nav">
          {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`sidebar__link ${
                location.pathname === path ? 'sidebar__link--active' : ''
              }`}
              onClick={() => setSidebarOpen(false)}
            >
              <Icon size={20} />
              <span>{label}</span>
            </Link>
          ))}
        </nav>

        <div className="sidebar__footer">
          <div className="sidebar__version">v1.0.0 — Prototype</div>
        </div>
      </aside>

      {/* Main content */}
      <div className="main-content">
        {/* Top bar */}
        <header className="topbar">
          <button
            className="topbar__menu-btn"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={24} />
          </button>
          <div className="topbar__breadcrumb">
            {NAV_ITEMS.find((n) => n.path === location.pathname)?.label || 'AI RoadGuard'}
          </div>
        </header>

        {/* Page content */}
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
