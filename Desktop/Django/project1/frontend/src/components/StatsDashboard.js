// src/components/StatsDashboard.js
// Simple statistics dashboard with basic charts

import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { api, formatNumber } from '../utils/api';

const StatsDashboard = () => {
    const [stats, setStats] = useState(null);
    const [instrumentStats, setInstrumentStats] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
    fetchAllStats();

    // Refresh stats every 30 seconds
    const interval = setInterval(fetchAllStats, 30000);
    return () => clearInterval(interval);
    }, []);

    const fetchAllStats = async () => {
    try {
        // Fetch overall order stats
        const orderStats = await api.getOrderStats();
        setStats(orderStats);

        // Fetch instruments and their individual stats
        const instruments = await api.getInstruments();
        
        const instrumentStatsPromises = instruments.slice(0, 8).map(async (instrument) => {
        try {
            const stats = await api.getInstrumentStats(instrument.id);
            return {
            symbol: instrument.symbol,
            name: instrument.name,
            order_count: stats.order_count || 0,
            total_volume: stats.total_volume || 0,
            avg_price: stats.avg_price || 0
            };
        } catch {
            return {
            symbol: instrument.symbol,
            name: instrument.name,
            order_count: 0,
            total_volume: 0,
            avg_price: 0
            };
        }
        });

        const instrumentStatsResults = await Promise.all(instrumentStatsPromises);
        setInstrumentStats(instrumentStatsResults);
        
        setError(null);
    } catch (err) {
        setError(err.message);
    } finally {
        setLoading(false);
    }
    };

    if (loading) return <div className="loading">Loading statistics...</div>;
    if (error) return <div className="error">Error loading stats: {error}</div>;
    if (!stats) return <div className="no-data">No statistics available</div>;

    return (
    <div className="stats-dashboard">
        <h2>Trading Statistics</h2>

        {/* Overall Stats Cards */}
        <div className="stats-grid">
        <div className="stat-card">
            <h3>Total Orders</h3>
            <div className="stat-value">{formatNumber(stats.total_orders)}</div>
        </div>

        <div className="stat-card active">
            <h3>Active Orders</h3>
            <div className="stat-value">{formatNumber(stats.active_orders)}</div>
        </div>

        <div className="stat-card filled">
            <h3>Filled Orders</h3>
            <div className="stat-value">{formatNumber(stats.filled_orders)}</div>
        </div>

        <div className="stat-card volume">
            <h3>Total Volume</h3>
            <div className="stat-value">{formatNumber(stats.total_volume)}</div>
        </div>
        </div>

        {/* Order Status Distribution */}
        <div className="stats-section">
        <h3>Order Status Distribution</h3>
        <div className="status-bars">
            <div className="status-bar">
            <span>Active:</span>
            <div className="bar-container">
                <div 
                className="bar active-bar" 
                style={{width: `${(stats.active_orders / stats.total_orders) * 100}%`}}
                ></div>
            </div>
            <span>{formatNumber(stats.active_orders)}</span>
            </div>

            <div className="status-bar">
            <span>Filled:</span>
            <div className="bar-container">
                <div 
                className="bar filled-bar" 
                style={{width: `${(stats.filled_orders / stats.total_orders) * 100}%`}}
                ></div>
            </div>
            <span>{formatNumber(stats.filled_orders)}</span>
            </div>

            <div className="status-bar">
            <span>Cancelled:</span>
            <div className="bar-container">
                <div 
                className="bar cancelled-bar" 
                style={{width: `${(stats.cancelled_orders / stats.total_orders) * 100}%`}}
                ></div>
            </div>
            <span>{formatNumber(stats.cancelled_orders)}</span>
            </div>
        </div>
        </div>

        {/* Volume by Instrument Chart */}
        <div className="stats-section">
        <h3>Volume by Instrument</h3>
        <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
            <BarChart data={instrumentStats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                dataKey="symbol" 
                tick={{ fontSize: 12 }}
                />
                <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => formatNumber(value)}
                />
                <Tooltip 
                formatter={(value, name) => [formatNumber(value), name]}
                labelStyle={{ color: '#333' }}
                />
                <Bar 
                dataKey="total_volume" 
                fill="#3B82F6" 
                name="Total Volume"
                />
            </BarChart>
            </ResponsiveContainer>
        </div>
        </div>

        {/* Instrument Details Table */}
        <div className="stats-section">
        <h3>Instrument Breakdown</h3>
        <table className="instruments-stats-table">
            <thead>
            <tr>
                <th>Symbol</th>
                <th>Name</th>
                <th>Orders</th>
                <th>Volume</th>
                <th>Avg Price</th>
            </tr>
            </thead>
            <tbody>
            {instrumentStats.map((inst) => (
                <tr key={inst.symbol}>
                <td className="symbol-cell">{inst.symbol}</td>
                <td className="name-cell">{inst.name}</td>
                <td className="number-cell">{formatNumber(inst.order_count)}</td>
                <td className="number-cell">{formatNumber(inst.total_volume)}</td>
                <td className="price-cell">
                    {inst.avg_price > 0 ? `$${formatPrice(inst.avg_price)}` : 'N/A'}
                </td>
                </tr>
            ))}
            </tbody>
        </table>
        </div>
    </div>
    );
};

export default StatsDashboard;