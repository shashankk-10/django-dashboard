// src/components/OrderBook.js
// Real-time order book display component

import React, { useState, useEffect } from 'react';
import { api, formatPrice, formatNumber } from '../utils/api';

const OrderBook = ({ instrumentId }) => {
    const [orderBook, setOrderBook] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);

    useEffect(() => {
    if (!instrumentId) return;

    const fetchOrderBook = async () => {
        try {
        const data = await api.getOrderBook(instrumentId);
        setOrderBook(data);
        setLastUpdate(new Date());
        setError(null);
        } catch (err) {
        setError(err.message);
        } finally {
        setLoading(false);
        }
    };

    // Initial fetch
    fetchOrderBook();

    // Auto-refresh every 3 seconds
    const interval = setInterval(fetchOrderBook, 3000);
    return () => clearInterval(interval);
    }, [instrumentId]);

    if (loading) return <div className="loading">Loading order book...</div>;
    if (error) return <div className="error">Error: {error}</div>;
    if (!orderBook) return <div className="no-data">No order book data</div>;

    const { bids, asks, spread, instrument } = orderBook;

    return (
    <div className="order-book">
        <div className="order-book-header">
        <h2>{instrument.symbol} - {instrument.name}</h2>
        {spread && (
            <div className="spread-info">
            <span>Best Bid: ${formatPrice(spread.best_bid)}</span>
            <span>Best Ask: ${formatPrice(spread.best_ask)}</span>
            <span>Spread: ${formatPrice(spread.absolute)} ({spread.percentage.toFixed(3)}%)</span>
            </div>
        )}
        {lastUpdate && (
            <div className="last-update">
            Last Update: {lastUpdate.toLocaleTimeString()}
            </div>
        )}
        </div>

        <div className="order-book-content">
        {/* Bids Table */}
        <div className="bids-section">
            <h3 className="bids-title">Bids (Buy Orders)</h3>
            <table className="order-table">
            <thead>
                <tr>
                <th>Price</th>
                <th>Quantity</th>
                <th>Orders</th>
                </tr>
            </thead>
            <tbody>
                {bids.slice(0, 10).map((bid, index) => (
                <tr key={index} className="bid-row">
                    <td className="price-cell bid-price">${formatPrice(bid.price)}</td>
                    <td className="quantity-cell">{formatNumber(bid.quantity)}</td>
                    <td className="orders-cell">{bid.order_count}</td>
                </tr>
                ))}
            </tbody>
            </table>
        </div>

        {/* Asks Table */}
        <div className="asks-section">
            <h3 className="asks-title">Asks (Sell Orders)</h3>
            <table className="order-table">
            <thead>
                <tr>
                <th>Price</th>
                <th>Quantity</th>
                <th>Orders</th>
                </tr>
            </thead>
            <tbody>
                {asks.slice(0, 10).map((ask, index) => (
                <tr key={index} className="ask-row">
                    <td className="price-cell ask-price">${formatPrice(ask.price)}</td>
                    <td className="quantity-cell">{formatNumber(ask.quantity)}</td>
                    <td className="orders-cell">{ask.order_count}</td>
                </tr>
                ))}
            </tbody>
            </table>
        </div>
        </div>
    </div>
    );
};

export default OrderBook;