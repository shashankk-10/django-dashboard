// src/pages/Dashboard.js
// Main dashboard page that combines all components

import React, { useState, useEffect } from 'react';
import OrderBook from '../components/OrderBook';
import OrderForm from '../components/OrderForm';
import OrderHistory from '../components/OrderHistory';
import StatsDashboard from '../components/StatsDashboard';
import { api } from '../utils/api';

const Dashboard = () => {
    const [instruments, setInstruments] = useState([]);
    const [selectedInstrument, setSelectedInstrument] = useState(null);
    const [activeTab, setActiveTab] = useState('orderbook');
    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchInstruments();
    }, []);

    const fetchInstruments = async () => {
        try {
        const data = await api.getInstruments();
        setInstruments(data);
        
        // Select first instrument by default
        if (data.length > 0) {
            setSelectedInstrument(data[0].id);
        }
        
        setError(null);
        } catch (err) {
        setError(err.message);
        } finally {
        setLoading(false);
        }
    };

    const handleOrderSubmit = () => {
        // Trigger refresh of other components
        setRefreshTrigger(prev => prev + 1);
    };

    const handleInstrumentChange = (e) => {
        setSelectedInstrument(parseInt(e.target.value));
    };

    const tabs = [
        { id: 'orderbook', label: 'Order Book', component: OrderBook },
        { id: 'orders', label: 'Place Order', component: OrderForm },
        { id: 'history', label: 'Order History', component: OrderHistory },
        { id: 'stats', label: 'Statistics', component: StatsDashboard }
    ];

    if (loading) {
        return <div className="app-loading">Loading trading dashboard...</div>;
    }

    if (error) {
        return (
        <div className="app-error">
            <h2>Failed to load dashboard</h2>
            <p>Error: {error}</p>
            <button onClick={fetchInstruments}>Retry</button>
        </div>
        );
    }

    return (
        <div className="dashboard">
        {/* Header */}
        <header className="dashboard-header">
            <h1>HFT Order Book Dashboard</h1>
            
            {/* Instrument Selector */}
            <div className="instrument-selector">
            <label htmlFor="instrument-select">Instrument:</label>
            <select
                id="instrument-select"
                value={selectedInstrument || ''}
                onChange={handleInstrumentChange}
            >
                <option value="">Select Instrument</option>
                {instruments.map(instrument => (
                <option key={instrument.id} value={instrument.id}>
                    {instrument.symbol} - {instrument.name}
                </option>
                ))}
            </select>
            </div>
        </header>

        {/* Navigation Tabs */}
        <nav className="dashboard-nav">
            {tabs.map(tab => (
            <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
            >
                {tab.label}
            </button>
            ))}
        </nav>

        {/* Main Content */}
        <main className="dashboard-content">
            {activeTab === 'orderbook' && (
            <OrderBook instrumentId={selectedInstrument} />
            )}
            
            {activeTab === 'orders' && (
            <OrderForm 
                instruments={instruments} 
                onOrderSubmit={handleOrderSubmit}
            />
            )}
            
            {activeTab === 'history' && (
            <OrderHistory 
                selectedInstrumentId={selectedInstrument}
                refreshTrigger={refreshTrigger}
            />
            )}
            
            {activeTab === 'stats' && (
            <StatsDashboard />
            )}
        </main>

        {/* Simple Status Footer */}
        <footer className="dashboard-footer">
            <div className="status-info">
            <span>Connected to: {process.env.REACT_APP_API_BASE_URL || 'localhost:8000'}</span>
            <span>•</span>
            <span>Instruments: {instruments.length}</span>
            <span>•</span>
            <span>Last Update: {new Date().toLocaleTimeString()}</span>
            </div>
        </footer>
        </div>
    );
};

export default Dashboard;