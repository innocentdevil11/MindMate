/**
 * API helper — MindMate.
 * 
 * Centralized HTTP client that auto-attaches the Supabase JWT token
 * to every request. Handles 401 errors by triggering auto-logout.
 * 
 * WHY centralized: Previously, page.jsx used bare fetch() without auth.
 * This module ensures every API call carries the user's token and
 * gracefully handles auth failures without duplicating logic.
 */

import { supabase } from './supabase'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Get the current session token, or null if not authenticated.
 */
async function getToken() {
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token || null
}

/**
 * Make an authenticated API request.
 * 
 * @param {string} path - API path (e.g., '/decision')
 * @param {object} options - fetch options
 * @returns {Promise<any>} - parsed JSON response
 * @throws {Error} - on network or API errors
 */
async function request(path, options = {}) {
    const token = await getToken()

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    }

    // Attach auth token if available
    if (token) {
        headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers,
    })

    // Handle 401 — token expired or invalid → force logout
    if (response.status === 401) {
        await supabase.auth.signOut()
        // Redirect to login (will be caught by AuthContext)
        if (typeof window !== 'undefined') {
            window.location.href = '/login'
        }
        throw new Error('Session expired. Please sign in again.')
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `API error: ${response.status}`)
    }

    return response.json()
}

// Convenience methods
export const api = {
    get: (path) => request(path, { method: 'GET' }),
    post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
    put: (path, body) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
}

export { API_URL }
