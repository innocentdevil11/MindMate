/**
 * API helper — MindMate.
 * 
 * Centralized HTTP client that auto-attaches the Supabase JWT token
 * to every request. Handles 401 errors with one silent token refresh retry.
 * 
 * WHY centralized: Previously, page.jsx used bare fetch() without auth.
 * This module ensures every API call carries the user's token and
 * gracefully handles auth failures without duplicating logic.
 */

import { supabase } from './supabase'

const rawApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim()
const PROD_API_FALLBACK = 'https://mindmate-api-pgco.onrender.com'
const LOCALHOST_URL_PATTERN = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i
const hasProdLocalhostUrl = process.env.NODE_ENV !== 'development' && rawApiUrl && LOCALHOST_URL_PATTERN.test(rawApiUrl)
const resolvedApiUrl = process.env.NODE_ENV === 'development'
    ? (rawApiUrl || 'http://localhost:8000')
    : (hasProdLocalhostUrl ? PROD_API_FALLBACK : (rawApiUrl || PROD_API_FALLBACK))
const API_URL = resolvedApiUrl.replace(/\/$/, '')

/**
 * Get the current session token, or null if not authenticated.
 */
async function getToken() {
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token || null
}

/**
 * Try to refresh and return a fresh access token.
 */
async function refreshToken() {
    try {
        const { data, error } = await supabase.auth.refreshSession()
        if (error) return null
        return data?.session?.access_token || null
    } catch {
        return null
    }
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms))
}

async function resolveToken() {
    // Session hydration can lag briefly right after login/redirect.
    for (let i = 0; i < 6; i++) {
        const token = await getToken()
        if (token) return token

        if (i === 1) {
            const refreshed = await refreshToken()
            if (refreshed) return refreshed
        }

        await sleep(200)
    }

    return null
}

/**
 * Make an authenticated API request.
 * 
 * @param {string} path - API path (e.g., '/decision')
 * @param {object} options - fetch options
 * @returns {Promise<any>} - parsed JSON response
 * @throws {Error} - on network or API errors
 */
async function request(path, options = {}, hasRetriedAuth = false) {
    const token = await resolveToken()
    if (!token) {
        await supabase.auth.signOut()
        if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
            window.location.href = '/login'
        }
        throw new Error('Authentication required. Please sign in again.')
    }

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    }

    // Attach auth token if available
    if (token) {
        headers['Authorization'] = `Bearer ${token}`
    }

    let response
    try {
        response = await fetch(`${API_URL}${path}`, {
            ...options,
            headers,
        })
    } catch {
        throw new Error(`Failed to reach API at ${API_URL}. Check URL, HTTPS, and backend CORS settings.`)
    }

    // Handle 401 — token expired or invalid → force logout
    if (response.status === 401) {
        if (!hasRetriedAuth) {
            const refreshedToken = await refreshToken()
            if (refreshedToken) {
                return request(path, options, true)
            }
        }
        const errorData = await response.json().catch(() => ({}))
        await supabase.auth.signOut()
        if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
            window.location.href = '/login'
        }
        throw new Error(errorData.detail || 'Unauthorized. Please sign in again.')
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
    patch: (path, body) => request(path, { method: 'PATCH', body: JSON.stringify(body) }),
}

export { API_URL }
