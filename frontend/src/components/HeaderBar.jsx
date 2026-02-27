import { useNavigate } from 'react-router-dom'

export default function HeaderBar({ players, onSync, syncing }) {
    const navigate = useNavigate()

    return (
        <header className="header-bar">
            <div className="header-logo">
                <span style={{ fontSize: '24px' }}>🏆</span>
                <h1>Triathlon Tracker</h1>
            </div>

            <div className="header-players">
                {players.map((p) => (
                    <div key={p.id} className="header-player">
                        {p.profile_photo ? (
                            <img src={p.profile_photo} alt={p.display_name} className="header-avatar" />
                        ) : (
                            <div
                                className="header-avatar"
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    background: 'var(--bg-secondary)',
                                    fontSize: '14px',
                                }}
                            >
                                {p.display_name.charAt(0)}
                            </div>
                        )}
                        <div style={{ opacity: p.status === 'connected' ? 1 : 0.6 }}>
                            <div style={{ fontSize: '13px', fontWeight: 600 }}>{p.display_name}</div>
                            {p.status === 'connected' ? (
                                <div style={{ fontSize: '11px', color: '#10b981' }}>● Connected</div>
                            ) : (
                                <a
                                    href="#"
                                    className="header-reconnect"
                                    onClick={(e) => {
                                        e.preventDefault()
                                        navigate('/login')
                                    }}
                                >
                                    Connect Strava
                                </a>
                            )}
                        </div>
                    </div>
                ))}

                <button
                    className="btn"
                    onClick={onSync}
                    disabled={syncing}
                    style={{
                        background: 'var(--bg-glass)',
                        border: '1px solid var(--border-glass)',
                        color: 'var(--text-secondary)',
                        fontSize: '13px',
                        padding: '8px 16px',
                    }}
                >
                    {syncing ? '⟳ Syncing...' : '🔄 Sync Strava'}
                </button>
            </div>
        </header>
    )
}
