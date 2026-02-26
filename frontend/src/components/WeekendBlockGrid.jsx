export default function WeekendBlockGrid({ players, blockScores, blocks }) {
    if (!players || players.length < 2) return null

    const p1 = players[0]
    const p2 = players[1]

    const blockOrder = ['block_1', 'block_2', 'block_3', 'block_4', 'block_5']
    const blockLabels = {
        block_1: 'Block 1 — Mar 1',
        block_2: 'Block 2 — Mar 6–8',
        block_3: 'Block 3 — Mar 13–15',
        block_4: 'Block 4 — Mar 20–22',
        block_5: 'Block 5 — Mar 27–29',
    }

    const allSports = ['Cycling', 'Running', 'Swimming']
    const block1Sports = ['Swimming']

    const scoreMap = {}
        ; (blockScores || []).forEach((s) => {
            scoreMap[s.block_id] = s
        })

    const blockMap = {}
        ; (blocks || []).forEach((b) => {
            blockMap[b.block_id] = b
        })

    function getCellClass(pts1, pts2) {
        if (pts1 === 2 && pts2 !== 2) return 'cell-winner'
        if (pts1 === 0 && pts2 === 2) return 'cell-loss'
        if (pts1 === 1) return 'cell-tie'
        if (pts1 === 2 && pts2 === 2) return 'cell-tie'
        return ''
    }

    function formatCals(val) {
        if (!val || val === 0) return '—'
        return val >= 1000 ? `${(val / 1000).toFixed(1)}k` : Math.round(val).toString()
    }

    return (
        <div className="glass-card block-grid">
            <div className="block-grid-title">📅 Weekend Block Grid</div>
            <table className="grid-table">
                <thead>
                    <tr>
                        <th>Block</th>
                        {allSports.map((sport) => (
                            <th key={sport}>{sport}</th>
                        ))}
                        <th>Bonus</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    {blockOrder.map((blockId) => {
                        const score = scoreMap[blockId]
                        const block = blockMap[blockId]
                        const isLocked = block?.locked || score?.locked
                        const sports = blockId === 'block_1' ? block1Sports : allSports

                        return (
                            <tr key={blockId}>
                                <td>
                                    <div className="block-label">
                                        {isLocked && <span className="lock-icon">🔒</span>}
                                        {blockLabels[blockId]}
                                    </div>
                                </td>
                                {allSports.map((sport) => {
                                    if (!sports.includes(sport)) {
                                        return (
                                            <td key={sport} style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                                                —
                                            </td>
                                        )
                                    }

                                    if (!score) {
                                        return (
                                            <td key={sport} style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                                                Pending
                                            </td>
                                        )
                                    }

                                    const cals1 = score.calories_by_sport?.[sport]?.[p1.id] || 0
                                    const cals2 = score.calories_by_sport?.[sport]?.[p2.id] || 0
                                    const pts1 = score.points_by_sport?.[sport]?.[p1.id] || 0
                                    const pts2 = score.points_by_sport?.[sport]?.[p2.id] || 0
                                    const cellClass = getCellClass(pts1, pts2)

                                    return (
                                        <td key={sport} className={cellClass}>
                                            <div className="cell-points">{pts1} — {pts2}</div>
                                            <div className="cell-calories">
                                                {formatCals(cals1)} vs {formatCals(cals2)} cal
                                            </div>
                                        </td>
                                    )
                                })}
                                <td>
                                    {!score ? (
                                        <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>—</span>
                                    ) : score.clean_sweep_achieved ? (
                                        <span style={{ color: 'var(--accent-gold)', fontWeight: 700 }}>⚡+1</span>
                                    ) : score.clean_sweep_eligible?.[p1.id] &&
                                        score.clean_sweep_eligible?.[p2.id] ? (
                                        <span style={{ color: 'var(--text-muted)' }}>🔒</span>
                                    ) : (
                                        <span style={{ color: 'var(--text-muted)' }}>—</span>
                                    )}
                                </td>
                                <td style={{ fontWeight: 800, fontSize: '16px' }}>
                                    {score ? (
                                        <>
                                            <span style={{ color: 'var(--strava-orange)' }}>
                                                {score.total_points?.[p1.id] || 0}
                                            </span>
                                            {' — '}
                                            <span style={{ color: 'var(--cycling-color)' }}>
                                                {score.total_points?.[p2.id] || 0}
                                            </span>
                                        </>
                                    ) : (
                                        <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>—</span>
                                    )}
                                </td>
                            </tr>
                        )
                    })}
                </tbody>
            </table>

            {/* Legend */}
            <div
                style={{
                    display: 'flex',
                    gap: '16px',
                    marginTop: '12px',
                    fontSize: '11px',
                    color: 'var(--text-muted)',
                    justifyContent: 'center',
                    flexWrap: 'wrap',
                }}
            >
                <span>
                    <span
                        style={{
                            display: 'inline-block',
                            width: 10,
                            height: 10,
                            borderRadius: 2,
                            background: 'var(--winner-bg)',
                            border: '1px solid var(--winner-color)',
                            marginRight: 4,
                        }}
                    />
                    Winner (2pts)
                </span>
                <span>
                    <span
                        style={{
                            display: 'inline-block',
                            width: 10,
                            height: 10,
                            borderRadius: 2,
                            background: 'var(--tie-bg)',
                            border: '1px solid var(--tie-color)',
                            marginRight: 4,
                        }}
                    />
                    Tie (1pt each)
                </span>
                <span>⚡+1 = Clean Sweep Bonus</span>
                <span>🔒 = Scores Locked</span>
            </div>
        </div>
    )
}
