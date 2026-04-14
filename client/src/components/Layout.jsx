import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useState } from 'react';
import { LayoutDashboard, Users, Folder, CalendarCheck, User, Menu, Zap, LogOut } from 'lucide-react';

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
    { path: '/clients', label: 'Clients', icon: <Users size={20} /> },
    { path: '/projects', label: 'Projects', icon: <Folder size={20} /> },
    { path: '/today', label: 'Today', icon: <CalendarCheck size={20} /> },
  ];

  return (
    <div className="app-layout" id="app-layout">
      {/* Mobile hamburger */}
      <button className="hamburger-btn" id="hamburger-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
        <Menu size={24} />
      </button>

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`} id="sidebar">
        <div className="sidebar-header">
          <h2 className="app-logo" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={22} color="var(--text-primary)" />
            <span>FreelanceFlow</span>
          </h2>
        </div>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) => `nav-item ${isActive ? 'nav-item-active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-info">
            <span className="user-icon"><User size={18} /></span>
            <span className="user-name">{user?.username}</span>
          </div>
          <button className="logout-btn" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }} id="logout-btn" onClick={handleLogout}>
            <LogOut size={16} /> Logout
          </button>
        </div>
      </aside>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}

      {/* Main content */}
      <main className="main-content" id="main-content">
        <Outlet />
      </main>
    </div>
  );
}
