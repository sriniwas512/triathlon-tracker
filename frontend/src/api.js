const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function apiFetch(path, options = {}) {
    const url = `${API_BASE}${path}`;
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `API error: ${res.status}`);
    }
    return res.json();
}

export const api = {
    // Auth
    getAuthStatus: () => apiFetch('/api/auth/status'),
    getStravaAuthUrl: (playerId) => apiFetch(`/api/auth/strava?player_id=${playerId}`),

    // Players
    getPlayers: () => apiFetch('/api/players'),
    registerPlayer: (displayName) =>
        apiFetch('/api/register', {
            method: 'POST',
            body: JSON.stringify({ display_name: displayName }),
        }),

    // Activities
    syncPlayer: (playerId) => apiFetch(`/api/activities/sync/${playerId}`, { method: 'POST' }),
    syncAll: () => apiFetch('/api/activities/sync-all', { method: 'POST' }),
    getActivities: (playerId) => apiFetch(`/api/activities/${playerId}`),

    // Scores
    getScores: () => apiFetch('/api/scores'),
    getScore: (blockId) => apiFetch(`/api/scores/${blockId}`),
    calculateScore: (blockId) => apiFetch(`/api/scores/calculate/${blockId}`, { method: 'POST' }),

    // Dashboard
    getDashboard: () => apiFetch('/api/dashboard'),

    // Blocks
    getBlocks: () => apiFetch('/api/blocks'),
};
