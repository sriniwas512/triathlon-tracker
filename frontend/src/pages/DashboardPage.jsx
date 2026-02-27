import { useState, useEffect } from 'react'
import { api } from '../api'
import HeaderBar from '../components/HeaderBar'
import ScoreboardPanel from '../components/ScoreboardPanel'
import WeekendBlockGrid from '../components/WeekendBlockGrid'
import SportBreakdownPanel from '../components/SportBreakdownPanel'
import ProjectionPanel from '../components/ProjectionPanel'
import DinnerDebtTracker from '../components/DinnerDebtTracker'

export default function DashboardPage() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [syncing, setSyncing] = useState(false)
    const [error, setError] = useState(null)

    const fetchDashboard = async () => {
        try {
            const dashData = await api.getDashboard()
            setData(dashData)
            setError(null)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchDashboard()
    }, [])

    const handleSync = async () => {
        setSyncing(true)
        try {
            await api.syncAll()
            await fetchDashboard()
        } catch (err) {
            console.error('Sync failed:', err)
        } finally {
            setSyncing(false)
        }
    }

    if (loading) {
        return (
            <div className="loading-container">
                <div className="spinner" />
                <p style={{ color: 'var(--text-secondary)' }}>Loading dashboard...</p>
            </div>
        )
    }

    if (error) {
        return (
            <div className="loading-container">
                <p style={{ color: '#ef4444', fontSize: '18px' }}>⚠️ {error}</p>
                <button className="btn btn-strava" onClick={fetchDashboard}>
                    Retry
                </button>
            </div>
        )
    }

    const { players, scoreboard, block_scores, blocks, sport_breakdown, projection } = data

    return (
        <div>
            <HeaderBar players={players} onSync={handleSync} syncing={syncing} />

            <div className="dashboard">
                <DinnerDebtTracker
                    players={players}
                    scoreboard={scoreboard}
                />

                <ScoreboardPanel
                    players={players}
                    scoreboard={scoreboard}
                    blockScores={block_scores}
                />

                <WeekendBlockGrid
                    players={players}
                    blockScores={block_scores}
                    blocks={blocks}
                />

                <div className="section-header">📊 Sport Breakdown</div>
                <SportBreakdownPanel
                    players={players}
                    breakdown={sport_breakdown}
                />

                {projection && (
                    <ProjectionPanel
                        players={players}
                        projection={projection}
                        scoreboard={scoreboard}
                    />
                )}
            </div>
        </div>
    )
}
