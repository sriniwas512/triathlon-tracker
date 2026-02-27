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

const sportConfig = {
    Cycling: {
        icon: '🚴',
        color1: 'rgba(252, 76, 2, 0.8)',
        color2: 'rgba(59, 130, 246, 0.8)',
        border1: '#FC4C02',
        border2: '#3b82f6',
    },
    Running: {
        icon: '🏃',
        color1: 'rgba(252, 76, 2, 0.8)',
        color2: 'rgba(16, 185, 129, 0.8)',
        border1: '#FC4C02',
        border2: '#10b981',
    },
    Swimming: {
        icon: '🏊',
        color1: 'rgba(252, 76, 2, 0.8)',
        color2: 'rgba(99, 102, 241, 0.8)',
        border1: '#FC4C02',
        border2: '#6366f1',
    },
}

function SportChart({ sport, players, breakdown }) {
    const config = sportConfig[sport]
    if (!config || players.length === 0) return null

    const p1 = players[0]
    const p2 = players[1]

    const calories1 = breakdown.cumulative_calories?.[p1.id]?.[sport] || 0
    const calories2 = p2 ? (breakdown.cumulative_calories?.[p2.id]?.[sport] || 0) : 0
    const points1 = breakdown.cumulative_points?.[p1.id]?.[sport] || 0
    const points2 = p2 ? (breakdown.cumulative_points?.[p2.id]?.[sport] || 0) : 0

    const calorieData = {
        labels: [p1.display_name, p2 ? p2.display_name : 'Waiting...'],
        datasets: [
            {
                label: 'Calories',
                data: [calories1, calories2],
                backgroundColor: [config.color1, config.color2],
                borderColor: [config.border1, config.border2],
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false,
            },
        ],
    }

    const options = {
        responsive: true,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: 'rgba(17, 24, 39, 0.95)',
                titleColor: '#f1f5f9',
                bodyColor: '#94a3b8',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                cornerRadius: 8,
                padding: 12,
                callbacks: {
                    label: (ctx) => {
                        const pid = players[ctx.dataIndex].id
                        const isEst = breakdown.cumulative_is_estimated?.[pid]?.[sport]
                        return `${Math.round(ctx.raw).toLocaleString()} cal${isEst ? '*' : ''}`
                    },
                },
            },
        },
        scales: {
            x: {
                ticks: { color: '#94a3b8', font: { size: 12, weight: '600' } },
                grid: { display: false },
                border: { display: false },
            },
            y: {
                ticks: {
                    color: '#64748b',
                    font: { size: 10 },
                    callback: (v) => (v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v),
                },
                grid: { color: 'rgba(255, 255, 255, 0.04)', drawBorder: false },
                border: { display: false },
            },
        },
    }

    return (
        <div className="glass-card sport-chart-card">
            <div className="sport-chart-title">
                <span className={`sport-icon ${sport.toLowerCase()}`}>{config.icon}</span>
                {sport}
            </div>
            <Bar data={calorieData} options={options} />
            <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-around',
                    marginTop: '12px',
                    fontSize: '12px',
                    color: 'var(--text-secondary)',
                }}
            >
                <span>{p1.display_name}: <strong>{points1}</strong> pts</span>
                {p2 && <span>{p2.display_name}: <strong>{points2}</strong> pts</span>}
                {!p2 && <span style={{ opacity: 0.5 }}>Waiting for Player 2...</span>}
            </div>
        </div>
    )
}

export default function SportBreakdownPanel({ players, breakdown }) {
    if (!breakdown) return null

    return (
        <div className="sport-breakdown">
            {['Cycling', 'Running', 'Swimming'].map((sport) => (
                <SportChart
                    key={sport}
                    sport={sport}
                    players={players}
                    breakdown={breakdown}
                />
            ))}
        </div>
    )
}
