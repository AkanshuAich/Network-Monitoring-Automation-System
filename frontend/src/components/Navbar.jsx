import React from 'react';
import { NavLink } from 'react-router-dom';

const navItems = [
    { path: '/', label: 'Dashboard', icon: '◉' },
    { path: '/alerts', label: 'Alerts', icon: '⚠' },
];

export default function Navbar() {
    return (
        <nav className="sticky top-0 z-50 glass-card rounded-none border-x-0 border-t-0 px-6 py-3">
            <div className="max-w-7xl mx-auto flex items-center justify-between">
                {/* Logo */}
                <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-500/25">
                        <span className="text-white text-lg font-bold">N</span>
                    </div>
                    <span className="text-lg font-bold bg-gradient-to-r from-white to-surface-200 bg-clip-text text-transparent">
                        NetMonitor
                    </span>
                </div>

                {/* Nav Links */}
                <div className="flex items-center gap-1">
                    {navItems.map(({ path, label, icon }) => (
                        <NavLink
                            key={path}
                            to={path}
                            className={({ isActive }) =>
                                `flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${isActive
                                    ? 'bg-brand-500/15 text-brand-400 shadow-inner'
                                    : 'text-surface-200 hover:text-white hover:bg-white/5'
                                }`
                            }
                        >
                            <span>{icon}</span>
                            {label}
                        </NavLink>
                    ))}
                </div>

                {/* Status Indicator */}
                <div className="flex items-center gap-2 text-xs text-surface-200">
                    <span className="status-dot status-dot-up"></span>
                    System Online
                </div>
            </div>
        </nav>
    );
}
