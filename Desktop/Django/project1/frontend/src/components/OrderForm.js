// src/components/OrderForm.js
// Simple order entry form component

import React, { useState } from 'react';
import { api } from '../utils/api';

const OrderForm = ({ instruments, onOrderSubmit }) => {
    const [formData, setFormData] = useState({
    instrument_symbol: '',
    order_type: 'BUY',
    price: '',
    original_quantity: '',
    client_order_id: ''
    });

    const [submitting, setSubmitting] = useState(false);
    const [message, setMessage] = useState('');
    const [messageType, setMessageType] = useState(''); // 'success' or 'error'

    const handleChange = (e) => {
    setFormData({
        ...formData,
        [e.target.name]: e.target.value
    });
    };

    const handleSubmit = async (e) => {
    e.preventDefault();

    // Basic validation
    if (!formData.instrument_symbol || !formData.price || !formData.original_quantity) {
        setMessage('Please fill in all required fields');
        setMessageType('error');
        return;
    }

    if (parseFloat(formData.price) <= 0) {
        setMessage('Price must be greater than 0');
        setMessageType('error');
        return;
    }

    if (parseInt(formData.original_quantity) <= 0) {
        setMessage('Quantity must be greater than 0');
        setMessageType('error');
        return;
    }

    setSubmitting(true);
    setMessage('');

    try {
        const result = await api.createOrder(formData);
        
        setMessage(`Order created successfully! Order ID: ${result.order_id}`);
        setMessageType('success');
        
        // Reset form
        setFormData({
        instrument_symbol: '',
        order_type: 'BUY',
        price: '',
        original_quantity: '',
        client_order_id: ''
        });
        
        // Notify parent component
        if (onOrderSubmit) {
        onOrderSubmit();
        }
        
    } catch (error) {
        setMessage(`Error: ${error.message}`);
        setMessageType('error');
    } finally {
        setSubmitting(false);
    }
    };

    return (
    <div className="order-form">
        <h2>Place New Order</h2>
        
        <form onSubmit={handleSubmit}>
        <div className="form-row">
            <div className="form-group">
            <label htmlFor="instrument_symbol">Instrument *</label>
            <select
                id="instrument_symbol"
                name="instrument_symbol"
                value={formData.instrument_symbol}
                onChange={handleChange}
                required
            >
                <option value="">Select Instrument</option>
                {instruments.map(instrument => (
                <option key={instrument.id} value={instrument.symbol}>
                    {instrument.symbol} - {instrument.name}
                </option>
                ))}
            </select>
            </div>

            <div className="form-group">
            <label htmlFor="order_type">Order Type</label>
            <select
                id="order_type"
                name="order_type"
                value={formData.order_type}
                onChange={handleChange}
            >
                <option value="BUY">Buy</option>
                <option value="SELL">Sell</option>
            </select>
            </div>
        </div>

        <div className="form-row">
            <div className="form-group">
            <label htmlFor="price">Price ($) *</label>
            <input
                type="number"
                id="price"
                name="price"
                value={formData.price}
                onChange={handleChange}
                step="0.01"
                min="0.01"
                placeholder="175.50"
                required
            />
            </div>

            <div className="form-group">
            <label htmlFor="original_quantity">Quantity *</label>
            <input
                type="number"
                id="original_quantity"
                name="original_quantity"
                value={formData.original_quantity}
                onChange={handleChange}
                min="1"
                placeholder="100"
                required
            />
            </div>
        </div>

        <div className="form-group">
            <label htmlFor="client_order_id">Client Order ID (Optional)</label>
            <input
            type="text"
            id="client_order_id"
            name="client_order_id"
            value={formData.client_order_id}
            onChange={handleChange}
            placeholder="CLIENT_12345"
            />
        </div>

        <button 
            type="submit" 
            disabled={submitting}
            className={`submit-btn ${formData.order_type.toLowerCase()}-order ${submitting ? 'disabled' : ''}`}
        >
            {submitting ? 'Placing Order...' : `Place ${formData.order_type} Order`}
        </button>
        </form>

        {message && (
        <div className={`message ${messageType}`}>
            {message}
        </div>
        )}
    </div>
    );
};

export default OrderForm;