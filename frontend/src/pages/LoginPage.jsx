import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api'

function PlayerCard({ player, onConnect }) {
    const isConnected = player.status === 'connected'

    const handleConnect = async () => {
        try {
            const data = await api.getStravaAuthUrl(player.id)
            window.location.href = data.redirect_url
        } catch (err) {
            console.error('Failed to get auth URL:', err)
        }
    }

    return (
        <div className="glass-card player-card">
            {isConnected && player.profile_photo ? (
                <img
                    src={player.profile_photo}
                    alt={player.display_name}
                    className="player-card-avatar"
                />
            ) : (
                <div
                    className="player-card-avatar"
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: 'var(--bg-glass)',
                        border: '2px dashed var(--text-muted)',
                        fontSize: '28px',
                        color: 'var(--text-muted)',
                    }}
                >
                    {player.display_name.charAt(0).toUpperCase()}
                </div>
            )}

            <h2 className="player-card-name">{player.display_name}</h2>

            {isConnected ? (
                <div className="player-card-status connected">
                    <span style={{ fontSize: '20px' }}>✓</span>
                    <span>
                        {player.strava_firstname} {player.strava_lastname}
                    </span>
                </div>
            ) : (
                <>
                    <button className="btn btn-strava" onClick={handleConnect}>
                        <svg width="20" height="20" viewBox="0 0 64 64" fill="white">
                            <path d="M41.03 47.852l-5.572-10.976h-8.172L41.03 64l13.736-27.124h-8.18" />
                            <path d="M27.898 21.944l7.564 14.928h11.124L27.898 0 9.234 36.876H20.35" opacity="0.6" />
                        </svg>
                        Connect with Strava
                    </button>
                    <div className="player-card-status pending">
                        <span>⏳</span>
                        <span>Awaiting connection</span>
                    </div>
                </>
            )}
        </div>
    )
}

export default function LoginPage() {
    const [players, setPlayers] = useState([])
    const [loading, setLoading] = useState(true)
    const [allConnected, setAllConnected] = useState(false)
    const navigate = useNavigate()
    const [searchParams] = useSearchParams()

    const fetchStatus = async () => {
        try {
            const data = await api.getAuthStatus()
            setPlayers(data.players)
            setAllConnected(data.all_connected)
        } catch (err) {
            console.error('Failed to fetch auth status:', err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchStatus()
    }, [])

    // Handle OAuth callback redirect
    useEffect(() => {
        const connected = searchParams.get('connected')
        if (connected) {
            fetchStatus()
        }
    }, [searchParams])

    if (loading) {
        return (
            <div className="loading-container">
                <div className="spinner" />
                <p style={{ color: 'var(--text-secondary)' }}>Loading players...</p>
            </div>
        )
    }

    return (
        <div className="login-page">
            <h1 className="login-title">🏊 🚴 🏃 Triathlon Tracker</h1>
            <p className="login-subtitle">March 2026 Challenge — Connect your Strava to begin</p>

            <div className="login-cards">
                {players.map((player) => (
                    <PlayerCard key={player.id} player={player} />
                ))}
            </div>

            <div className="login-proceed">
                <button
                    className="btn btn-proceed"
                    disabled={!allConnected}
                    onClick={() => navigate('/dashboard')}
                >
                    {allConnected ? '🚀 Enter Dashboard' : '🔒 Connect all athletes to continue'}
                </button>
            </div>
        </div>
    )
}
