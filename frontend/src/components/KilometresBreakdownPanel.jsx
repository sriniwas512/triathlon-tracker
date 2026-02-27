import { Bar } from 'react-chartjs-2'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const sportConfigs = {
    Cycling: {
        unit: 'km',
        divisor: 1000,
        color1: 'rgba(59, 130, 246, 0.8)',
        color2: 'rgba(99, 102, 241, 0.8)',
        border1: '#3b82f6',
        border2: '#6366f1',
    },
    Running: {
        unit: 'km',
        divisor: 1000,
        color1: 'rgba(16, 185, 129, 0.8)',
        color2: 'rgba(34, 197, 94, 0.8)',
        border1: '#10b981',
        border2: '#22c55e',
    },
    Swimming: {
        unit: 'm',
        divisor: 1,
        color1: 'rgba(99, 102, 241, 0.8)',
        color2: 'rgba(59, 130, 246, 0.8)',
        border1: '#6366f1',
        border2: '#3b82f6',
    },
}

function KilometresChart({ sport, players, blockScores, totalDistance }) {
    const config = sportConfigs[sport]
    if (!config || players.length === 0) return null

    const p1 = players[0]
    const p2 = players[1]

    const blockOrder = ['block_1', 'block_2', 'block_3', 'block_4', 'block_5']
    const labels = ['B1', 'B2', 'B3', 'B4', 'B5']

    const data1 = blockOrder.map(bid => {
        const score = blockScores.find(s => s.block_id === bid)
        const dist = score?.details_by_player_sport?.[p1.id]?.[sport]?.distance || 0
        return (dist / config.divisor).toFixed(1)
    })

    const data2 = p2 ? blockOrder.map(bid => {
        const score = blockScores.find(s => s.block_id === bid)
        const dist = score?.details_by_player_sport?.[p2.id]?.[sport]?.distance || 0
        return (dist / config.divisor).toFixed(1)
    }) : blockOrder.map(() => 0)

    const chartData = {
        labels,
        datasets: [
            {
                label: p1.display_name,
                data: data1,
                backgroundColor: config.color1,
                borderColor: config.border1,
                borderWidth: 1,
                borderRadius: 4,
            },
            {
                label: p2 ? p2.display_name : 'Waiting...',
                data: data2,
                backgroundColor: config.color2,
                borderColor: config.border2,
                borderWidth: 1,
                borderRadius: 4,
            },
        ],
    }

    const options = {
        responsive: true,
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: (ctx) => `${ctx.dataset.label}: ${ctx.raw}${config.unit}`,
                },
            },
        },
        scales: {
            x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } },
            y: {
                beginAtZero: true,
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: '#64748b', font: { size: 10 } }
            },
        },
    }

    const total1 = ((totalDistance?.[p1.id]?.[sport] || 0) / config.divisor).toFixed(1)
    const total2 = p2 ? ((totalDistance?.[p2.id]?.[sport] || 0) / config.divisor).toFixed(1) : 0

    return (
        <div className="glass-card distance-chart-card">
            <div className="distance-chart-title">{sport} ({config.unit})</div>
            <div className="distance-summary">
                <span>{p1.display_name}: <strong>{total1}{config.unit}</strong></span>
                {p2 && <span> vs {p2.display_name}: <strong>{total2}{config.unit}</strong></span>}
            </div>
            <Bar data={chartData} options={options} />
        </div>
    )
}

export default function KilometresBreakdownPanel({ players, blockScores, sportBreakdown }) {
    const hasData = Object.values(sportBreakdown?.cumulative_distance || {}).some(
        playerDist => Object.values(playerDist).some(d => d > 0)
    )

    if (!hasData) {
        return (
            <div className="glass-card no-data-card">
                <div className="section-header">📏 Kilometres Breakdown</div>
                <p style={{ color: 'var(--text-muted)', textAlign: 'center' }}>No distance data available yet. Sync your Strava activities to see the breakdown!</p>
            </div>
        )
    }

    return (
        <div className="kilometres-breakdown">
            <div className="section-header">📏 Kilometres Breakdown</div>
            <div className="distance-charts-container">
                {['Cycling', 'Running', 'Swimming'].map(sport => (
                    <KilometresChart
                        key={sport}
                        sport={sport}
                        players={players}
                        blockScores={blockScores}
                        totalDistance={sportBreakdown.cumulative_distance}
                    />
                ))}
            </div>
        </div>
    )
}
