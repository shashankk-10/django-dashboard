// src/utils/api.js
// Simple API utility functions for backend communication

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

// Generic API call function
const apiCall = async (endpoint, options = {}) => {
    try {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
        headers: {
        'Content-Type': 'application/json',
        ...options.headers,
        },
        ...options,
    };

    const response = await fetch(url, config);

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
    } catch (error) {
    console.error(`API Error for ${endpoint}:`, error);
    throw error;
    }
};

// Specific API functions
export const api = {
    // Instruments
    getInstruments: () => apiCall('/instruments/'),
    getInstrument: (id) => apiCall(`/instruments/${id}/`),
    getInstrumentStats: (id) => apiCall(`/instruments/${id}/stats/`),

    // Orders
    getOrders: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiCall(`/orders/${queryString ? `?${queryString}` : ''}`);
    },
    createOrder: (orderData) => apiCall('/orders/', {
    method: 'POST',
    body: JSON.stringify(orderData),
    }),
    getOrder: (id) => apiCall(`/orders/${id}/`),
    cancelOrder: (id) => apiCall(`/orders/${id}/cancel/`, {
    method: 'PATCH',
    }),
    getOrderHistory: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiCall(`/orders/history/${queryString ? `?${queryString}` : ''}`);
    },
    getOrderStats: () => apiCall('/orders/stats/'),

    // Order Book
    getOrderBook: (instrumentId) => apiCall(`/orderbook/${instrumentId}/`),

    // Trades
    getTrades: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiCall(`/trades/${queryString ? `?${queryString}` : ''}`);
    },

    // Health Check
    healthCheck: () => apiCall('/health/'),
};

// Utility functions
export const formatPrice = (price) => {
    return parseFloat(price).toFixed(2);
};

export const formatNumber = (num) => {
    return new Intl.NumberFormat().format(num);
};

export const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString();
};