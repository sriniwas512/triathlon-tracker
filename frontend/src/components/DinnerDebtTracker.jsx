import { useState, useEffect } from 'react'

export default function DinnerDebtTracker({ players, scoreboard }) {
    const [timeLeft, setTimeLeft] = useState('')

    // Target: March 30, 2026, 00:00 SGT (UTC+8)
    // March 30, 2026, 00:00 SGT is March 29, 2026, 16:00:00 UTC
    const targetDate = new Date('2026-03-30T00:00:00+08:00')

    useEffect(() => {
        const timer = setInterval(() => {
            const now = new Date()
            const diff = targetDate - now

            if (diff <= 0) {
                setTimeLeft('Competition Ended')
                clearInterval(timer)
                return
            }

            const days = Math.floor(diff / (1000 * 60 * 60 * 24))
            const hours = Math.floor((diff / (1000 * 60 * 60)) % 24)
            const minutes = Math.floor((diff / (1000 * 60)) % 60)
            const seconds = Math.floor((diff / 1000) % 60)

            setTimeLeft(`${days}d ${hours}h ${minutes}m ${seconds}s`)
        }, 1000)

        return () => clearInterval(timer)
    }, [])

    if (!scoreboard || players.length === 0) return null

    const p1 = players[0]
    const p2 = players[1]
    const t1 = scoreboard.totals?.[p1.id] || 0
    const t2 = p2 ? (scoreboard.totals?.[p2.id] || 0) : 0

    const isTied = t1 === t2
    const gap = Math.abs(t1 - t2)
    const p1Losing = t1 < t2
    const loser = p1Losing ? p1 : p2

    // Messages
    let loserMessage = '🤝 Too close to call — both wallets are safe... for now'
    if (gap === 1) loserMessage = `${loser?.strava_firstname || loser?.display_name} is slightly concerned about their wallet 😰`
    else if (gap === 2) loserMessage = `${loser?.strava_firstname || loser?.display_name} is Googling Michelin star restaurants 😟`
    else if (gap === 3) loserMessage = `${loser?.strava_firstname || loser?.display_name} is checking their credit card limit 😨`
    else if (gap === 4) loserMessage = `${loser?.strava_firstname || loser?.display_name} has called their bank for an emergency credit increase 😱`
    else if (gap >= 5) loserMessage = `${loser?.strava_firstname || loser?.display_name} has started selling furniture to afford dinner 💀`

    // Restaurants
    let venue = '🍜 Hawker Centre'
    if (gap === 1) venue = '🍽️ Casual Restaurant'
    else if (gap === 2) venue = '👔 Smart Casual Dining'
    else if (gap === 3) venue = '🥂 Fine Dining'
    else if (gap === 4) venue = '⭐ 1 Michelin Star'
    else if (gap === 5) venue = '⭐⭐ 2 Michelin Stars'
    else if (gap >= 6) venue = '⭐⭐⭐ 3 Michelin Stars — Tasting Menu with Wine Pairing'

    const debtAmount = gap * 50
    const countdownLabel = isTied
        ? '⏰ Time left to decide who pays'
        : (p1Losing ? '⏰ Time left to avoid bankruptcy' : '⏰ Time left to seal the deal')

    // Dynamic Style
    let statusClass = 'debt-neutral'
    if (gap >= 1 && gap <= 2) statusClass = 'debt-amber'
    if (gap >= 3) statusClass = 'debt-red'
    if (isTied) statusClass = 'debt-green'

    return (
        <div className={`glass-card dinner-debt-tracker ${statusClass}`}>
            <div className="debt-title">💸 Dinner Debt Tracker</div>

            <div className="debt-loser-banner">
                {isTied ? (
                    <div className="debt-message-tied">{loserMessage}</div>
                ) : (
                    <div className="debt-message-loser">{loserMessage}</div>
                )}
            </div>

            <div className="debt-metrics">
                <div className="debt-metric-item">
                    <div className="debt-label">Current Stakes</div>
                    <div className="debt-venue">{venue}</div>
                </div>

                <div className="debt-metric-item">
                    <div className="debt-label">Dinner Debt</div>
                    <div className="debt-amount pulse">
                        {isTied ? '$0 — No debt yet' : `Estimated bill: $${debtAmount} SGD and climbing... 💸`}
                    </div>
                </div>
            </div>

            <div className="debt-countdown">
                <div className="debt-label">{countdownLabel}</div>
                <div className="debt-timer">{timeLeft}</div>
            </div>
        </div>
    )
}
