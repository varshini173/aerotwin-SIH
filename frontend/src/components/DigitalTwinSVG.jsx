export default function DigitalTwinSVG({ sensors }) {
  const { rpm = 4200, temperature = 72, vibration = 1.2 } = sensors || {}

  const cylinderClass =
    temperature > 110 ? 'status-critical' : temperature > 95 ? 'status-warning' : 'status-normal'
  const crankClass = vibration > 7 ? 'status-critical' : vibration > 4 ? 'status-warning' : 'status-normal'

  return (
    <svg
      viewBox="0 0 200 200"
      className="w-full h-full max-h-64"
      style={{ filter: 'drop-shadow(0 0 20px rgba(0,219,233,0.1))' }}
    >
      <defs>
        <linearGradient id="engineGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#32353c" />
          <stop offset="100%" stopColor="#191c22" />
        </linearGradient>
      </defs>
      <rect x="50" y="80" width="100" height="80" rx="4" fill="url(#engineGrad)" stroke="#849495" strokeWidth="2" />

      <path d="M 60 50 L 80 50 L 90 80 L 50 80 Z" className={`twin-part ${cylinderClass}`} opacity="0.8" />
      <path d="M 120 50 L 140 50 L 150 80 L 110 80 Z" className={`twin-part ${cylinderClass}`} opacity="0.8" />

      <circle
        cx="100"
        cy="140"
        r="25"
        fill="none"
        stroke="#b9cacb"
        strokeWidth="2"
        strokeDasharray="4 2"
        className={vibration > 5 ? 'animate-spin' : ''}
        style={{ animationDuration: `${2 / Math.max(0.1, vibration)}s` }}
      />
      <circle cx="100" cy="140" r="10" className={`twin-part ${crankClass}`} />

      <ellipse
        cx="160"
        cy="140"
        rx="15"
        ry="30"
        fill="none"
        stroke="#00f0ff"
        strokeWidth="2"
        className="origin-center"
        style={{ transform: `rotate(${rpm / 20}deg)`, transition: 'transform 0.1s linear' }}
      />
    </svg>
  )
}
