export default function ProjectionPanel({ players, projection, scoreboard }) {
    if (!projection || players.length === 0) return null

    const p1 = players[0]
    const p2 = players[1]

    const projWinner = projection.projected_winner
    const winnerName = players.find((p) => p.id === projWinner)?.display_name || 'Unknown'

    return (
        <div className="glass-card projection-panel">
            <div className="projection-title">🔮 Score Projection</div>

            {projWinner ? (
                <div className="projection-text">
                    At current pace,{' '}
                    <span className="projection-highlight">{winnerName}</span>{' '}
                    wins by{' '}
                    <span className="projection-highlight">
                        {projection.projected_margin} points
                    </span>
                </div>
            ) : (
                <div className="projection-text">
                    Projected to be a <span className="projection-highlight">tie!</span>
                </div>
            )}

            <div className="projection-detail">
                <strong>Projected Totals:</strong>{' '}
                {p1.display_name}: {projection.projected_totals?.[p1.id] || 0} pts
                {p2 && ` • ${p2.display_name}: ${projection.projected_totals?.[p2.id] || 0} pts`}
            </div>

            <div className="projection-detail" style={{ marginTop: '8px' }}>
                <strong>Remaining blocks:</strong> {projection.remaining_blocks} •{' '}
                <strong>Avg bonus rate:</strong> {projection.avg_bonus_rate} per block
            </div>

            {projection.clean_sweep_can_change_outcome && (
                <div className="projection-warning">
                    ⚠️ A clean sweep in remaining blocks could still change the outcome!
                </div>
            )}
        </div>
    )
}
