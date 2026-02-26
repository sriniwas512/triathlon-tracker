export default function ScoreboardPanel({ players, scoreboard, blockScores }) {
    if (!scoreboard || players.length < 2) return null

    const p1 = players[0]
    const p2 = players[1]
    const t1 = scoreboard.totals?.[p1.id] || 0
    const t2 = scoreboard.totals?.[p2.id] || 0
    const p1Leading = t1 > t2
    const p2Leading = t2 > t1

    // Find clean sweep blocks
    const sweepBlocks = (blockScores || []).filter(
        (s) => s.clean_sweep_achieved && s.locked
    )

    return (
        <div className="glass-card scoreboard">
            <div className="scoreboard-title">🏆 Competition Scoreboard</div>

            <div className="scoreboard-scores">
                <div className="scoreboard-player">
                    <div className="scoreboard-player-name">{p1.display_name}</div>
                    <div className={`scoreboard-player-score ${p1Leading ? 'leading' : ''}`}>
                        {t1}
                    </div>
                </div>
                <div className="scoreboard-vs">vs</div>
                <div className="scoreboard-player">
                    <div className="scoreboard-player-name">{p2.display_name}</div>
                    <div className={`scoreboard-player-score ${p2Leading ? 'leading' : ''}`}>
                        {t2}
                    </div>
                </div>
            </div>

            {scoreboard.is_tied ? (
                <div className="tied-banner">⚖️ It's a Tie!</div>
            ) : (
                <div className="winner-banner">
                    👑{' '}
                    {p1Leading ? p1.display_name : p2.display_name} leads by{' '}
                    {scoreboard.margin} point{scoreboard.margin !== 1 ? 's' : ''}
                </div>
            )}

            {sweepBlocks.length > 0 && (
                <div className="clean-sweep-badges">
                    {sweepBlocks.map((s) => {
                        const winner = players.find((p) => p.id === s.clean_sweep_winner)
                        return (
                            <div key={s.block_id} className="sweep-badge">
                                ⚡ {winner?.display_name} — {s.block_id.replace('_', ' ').replace('b', 'B')}
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
