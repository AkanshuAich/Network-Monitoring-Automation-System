import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import HostDetail from './pages/HostDetail';
import Alerts from './pages/Alerts';

export default function App() {
    return (
        <Router>
            <div className="min-h-screen bg-surface-900">
                <Navbar />
                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/hosts/:id" element={<HostDetail />} />
                        <Route path="/alerts" element={<Alerts />} />
                    </Routes>
                </main>
            </div>
        </Router>
    );
}
