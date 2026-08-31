import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

export default function TimeSeriesChart({ data, dataKey, label, color = '#00dbe9', unit = '', height = 160, padding = 0 }) {
  // Without a fixed minimum range, Recharts auto-scales the Y-axis tightly
  // around whatever's on screen -- so even trivial, expected sensor jitter
  // (a few RPM, a fraction of a degree) can visually swing the line from
  // the bottom to the top of the chart and look like dramatic movement.
  // `padding` guarantees the axis never zooms in tighter than that amount
  // around the real data, while still expanding normally to show a genuine
  // degradation trend once one actually develops.
  const domain = padding
    ? [(dataMin) => dataMin - padding, (dataMax) => dataMax + padding]
    : ['auto', 'auto']

  return (
    <div className="glass-card p-3">
      <div className="font-label-caps text-label-caps text-on-surface-variant mb-2">{label}</div>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#3b494b" opacity={0.3} />
          <XAxis dataKey="tick" tick={false} stroke="#3b494b" />
          <YAxis
            tick={{ fill: '#b9cacb', fontSize: 10 }}
            stroke="#3b494b"
            width={40}
            domain={domain}
            allowDataOverflow={false}
          />
          <Tooltip
            contentStyle={{
              background: '#1d2026',
              border: '1px solid #3b494b',
              borderRadius: 6,
              fontSize: 12,
            }}
            labelFormatter={() => ''}
            formatter={(value) => [`${value}${unit}`, label]}
          />
          <Line type="monotone" dataKey={dataKey} stroke={color} dot={false} strokeWidth={2} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
