// src/components/OrderHistory.js
// Order history table with basic filtering

import React, { useState, useEffect } from 'react';
import { api, formatPrice, formatNumber, formatDateTime } from '../utils/api';

const OrderHistory = ({ selectedInstrumentId, refreshTrigger }) => {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [filter, setFilter] = useState({
    status: '',
    order_type: '',
    days: '7'
    });

    useEffect(() => {
    fetchOrders();
    }, [selectedInstrumentId, currentPage, filter, refreshTrigger]);

    const fetchOrders = async () => {
    setLoading(true);
    try {
        const params = {
        page: currentPage,
        days: filter.days,
        ...(filter.status && { status: filter.status }),
        ...(filter.order_type && { order_type: filter.order_type }),
        };

        // Add instrument filter if specific instrument selected
        if (selectedInstrumentId) {
        // Get instrument symbol first
        const instrument = await api.getInstrument(selectedInstrumentId);
        params.instrument_symbol = instrument.symbol;
        }

        const data = await api.getOrderHistory(params);
        
        setOrders(data.results || []);
        if (data.count) {
        setTotalPages(Math.ceil(data.count / 50));
        }
        setError(null);
    } catch (err) {
        setError(err.message);
        setOrders([]);
    } finally {
        setLoading(false);
    }
    };

    const handleFilterChange = (e) => {
    setFilter({
        ...filter,
        [e.target.name]: e.target.value
    });
    setCurrentPage(1); // Reset to first page when filtering
    };

    const getStatusClass = (status) => {
    switch (status) {
        case 'ACTIVE': return 'status-active';
        case 'FILLED': return 'status-filled';
        case 'CANCELLED': return 'status-cancelled';
        case 'PARTIAL': return 'status-partial';
        default: return 'status-default';
    }
    };

    const getOrderTypeClass = (orderType) => {
    return orderType === 'BUY' ? 'order-type-buy' : 'order-type-sell';
    };

    return (
    <div className="order-history">
        <h2>Order History</h2>
        
        {/* Simple Filters */}
        <div className="filters">
        <div className="filter-group">
            <label>Status:</label>
            <select name="status" value={filter.status} onChange={handleFilterChange}>
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="FILLED">Filled</option>
            <option value="CANCELLED">Cancelled</option>
            <option value="PARTIAL">Partial</option>
            </select>
        </div>

        <div className="filter-group">
            <label>Type:</label>
            <select name="order_type" value={filter.order_type} onChange={handleFilterChange}>
            <option value="">Buy & Sell</option>
            <option value="BUY">Buy Only</option>
            <option value="SELL">Sell Only</option>
            </select>
        </div>

        <div className="filter-group">
            <label>Period:</label>
            <select name="days" value={filter.days} onChange={handleFilterChange}>
            <option value="1">Last 24 hours</option>
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="">All time</option>
            </select>
        </div>
        </div>

        {loading && <div className="loading">Loading orders...</div>}
        {error && <div className="error">Error: {error}</div>}

        {!loading && !error && (
        <>
            <div className="orders-table-container">
            <table className="orders-table">
                <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Type</th>
                    <th>Price</th>
                    <th>Original Qty</th>
                    <th>Filled Qty</th>
                    <th>Status</th>
                    <th>Created</th>
                </tr>
                </thead>
                <tbody>
                {orders.map((order) => (
                    <tr key={order.id}>
                    <td className="symbol-cell">{order.instrument_symbol}</td>
                    <td>
                        <span className={`order-type ${getOrderTypeClass(order.order_type)}`}>
                        {order.order_type}
                        </span>
                    </td>
                    <td className="price-cell">${formatPrice(order.price)}</td>
                    <td className="quantity-cell">{formatNumber(order.original_quantity)}</td>
                    <td className="quantity-cell">{formatNumber(order.filled_quantity)}</td>
                    <td>
                        <span className={`status ${getStatusClass(order.status)}`}>
                        {order.status}
                        </span>
                    </td>
                    <td className="date-cell">{formatDateTime(order.created_at)}</td>
                    </tr>
                ))}
                </tbody>
            </table>
            </div>

            {/* Simple Pagination */}
            {totalPages > 1 && (
            <div className="pagination">
                <button
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="pagination-btn"
                >
                Previous
                </button>
                
                <span className="pagination-info">
                Page {currentPage} of {totalPages}
                </span>
                
                <button
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="pagination-btn"
                >
                Next
                </button>
            </div>
            )}

            {orders.length === 0 && (
            <div className="no-data">
                No orders found for the selected filters.
            </div>
            )}
        </>
        )}
    </div>
    );
};

export default OrderHistory;