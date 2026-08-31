import { useEffect, useState } from 'react'
import { useEngineSocket } from '../hooks/useEngineSocket'
import TimeSeriesChart from '../charts/TimeSeriesChart'
import AlertFeed from '../components/AlertFeed'
import { api } from '../services/api'

export default function LiveMonitoring() {
  const [dataSource, setDataSource] = useState('software')

  // Arduino connection popup state
  const [showArduinoModal, setShowArduinoModal] = useState(false)
  const [serialPorts, setSerialPorts] = useState([])
  const [selectedPort, setSelectedPort] = useState('')
  const [serialConnecting, setSerialConnecting] = useState(false)
  const [serialError, setSerialError] = useState('')

  const { state, history } = useEngineSocket(200)
  const s = state || {}
  const chartData = history.map((h, i) => ({ ...h, tick: i }))

  // Load current source
  useEffect(() => {
    api.getSource()
      .then((data) => {
        if (data.source) {
          setDataSource(data.source)
        }
      })
      .catch((error) => {
        console.error('Failed to get data source:', error)
      })
  }, [])

  // Switch back to software
  const changeToSoftware = async () => {
    try {
      await api.setSource('software')
      await api.disconnectSerial()

      setDataSource('software')
    } catch (error) {
      console.error('Failed to switch to software:', error)
    }
  }

  // Open Arduino popup and load COM ports
  const openArduinoModal = async () => {
    setSerialError('')
    setSelectedPort('')

    try {
      const data = await api.getSerialPorts()

      setSerialPorts(data.ports || [])
      setShowArduinoModal(true)
    } catch (error) {
      console.error('Failed to get serial ports:', error)
      setSerialError('Could not detect serial ports.')
      setShowArduinoModal(true)
    }
  }

  // Refresh available COM ports
  const refreshPorts = async () => {
    setSerialError('')

    try {
      const data = await api.getSerialPorts()
      setSerialPorts(data.ports || [])
    } catch (error) {
      console.error('Failed to refresh serial ports:', error)
      setSerialError('Could not detect serial ports.')
    }
  }

  // Connect selected Arduino
  const connectArduino = async () => {
    if (!selectedPort) {
      setSerialError('Please select a serial port.')
      return
    }

    setSerialConnecting(true)
    setSerialError('')

    try {
      const result = await api.connectSerial(selectedPort)

      if (result.connected) {
        setDataSource('arduino')
        setShowArduinoModal(false)
      } else {
        setSerialError(
          result.error || 'Could not connect to the selected Arduino.'
        )
      }
    } catch (error) {
      console.error('Arduino connection failed:', error)
      setSerialError(
        error.message || 'Could not connect to the selected Arduino.'
      )
    } finally {
      setSerialConnecting(false)
    }
  }

  return (
    <div className="flex flex-col gap-stack-md h-full">

      {/* DATA SOURCE */}
      <div className="glass-card p-4 flex items-center justify-between">
        <div>
          <div className="font-label-caps text-label-caps text-on-surface-variant">
            DATA SOURCE
          </div>

          <div className="font-data-lg text-headline-md text-primary">
            {dataSource === 'software'
              ? 'SOFTWARE SIMULATION'
              : 'ARDUINO HARDWARE'}
          </div>
        </div>

        <div className="flex gap-2">

          {/* SOFTWARE */}
          <button
            type="button"
            onClick={changeToSoftware}
            className={`px-4 py-2 rounded-lg font-label-caps transition ${
              dataSource === 'software'
                ? 'bg-primary text-on-primary'
                : 'glass-card text-on-surface-variant'
            }`}
          >
            SOFTWARE
          </button>

          {/* ARDUINO */}
          <button
            type="button"
            onClick={openArduinoModal}
            className={`px-4 py-2 rounded-lg font-label-caps transition ${
              dataSource === 'arduino'
                ? 'bg-primary text-on-primary'
                : 'glass-card text-on-surface-variant'
            }`}
          >
            ARDUINO
          </button>

        </div>
      </div>

      {/* ARDUINO SERIAL PORT MODAL */}
      {showArduinoModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">

          <div className="glass-card w-full max-w-md p-6">

            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="font-label-caps text-label-caps text-on-surface-variant">
                  HARDWARE CONNECTION
                </div>

                <div className="font-data-lg text-headline-md text-primary">
                  ARDUINO UNO
                </div>
              </div>

              <button
                type="button"
                onClick={() => setShowArduinoModal(false)}
                className="text-on-surface-variant text-xl"
              >
                ×
              </button>
            </div>

            <div className="mb-2 font-label-caps text-label-caps text-on-surface-variant">
              SELECT SERIAL PORT
            </div>

            {serialPorts.length > 0 ? (
              <select
                value={selectedPort}
                onChange={(e) => setSelectedPort(e.target.value)}
                className="w-full p-3 rounded-lg mb-4 bg-surface text-on-surface"
              >
                <option value="">
                  Select Arduino port
                </option>

                {serialPorts.map((item) => (
                  <option
                    key={item.port}
                    value={item.port}
                  >
                    {item.port} — {item.description}
                  </option>
                ))}
              </select>
            ) : (
              <div className="p-4 rounded-lg mb-4 glass-card text-on-surface-variant">
                No serial ports detected.
                <br />
                Make sure the Arduino UNO is plugged in.
              </div>
            )}

            {serialError && (
              <div className="mb-4 p-3 rounded-lg text-sm text-red-300 bg-red-950/30">
                {serialError}
              </div>
            )}

            <div className="flex justify-between gap-3">

              <button
                type="button"
                onClick={refreshPorts}
                className="px-4 py-2 rounded-lg glass-card text-on-surface-variant"
              >
                REFRESH
              </button>

              <div className="flex gap-2">

                <button
                  type="button"
                  onClick={() => setShowArduinoModal(false)}
                  className="px-4 py-2 rounded-lg glass-card text-on-surface-variant"
                >
                  CANCEL
                </button>

                <button
                  type="button"
                  disabled={!selectedPort || serialConnecting}
                  onClick={connectArduino}
                  className="px-4 py-2 rounded-lg bg-primary text-on-primary disabled:opacity-50"
                >
                  {serialConnecting ? 'CONNECTING...' : 'CONNECT'}
                </button>

              </div>
            </div>

          </div>
        </div>
      )}

      {/* EXISTING DASHBOARD */}
      <div className="grid grid-cols-4 gap-gutter">
        <div className="glass-card p-3 text-center">
          <div className="font-label-caps text-label-caps text-on-surface-variant">
            ANOMALY SCORE
          </div>
          <div className="font-data-lg text-display-lg text-primary">
            {s.anomalyScore ?? 0}
          </div>
        </div>

        <div className="glass-card p-3 text-center">
          <div className="font-label-caps text-label-caps text-on-surface-variant">
            CURRENT PREDICTION
          </div>
          <div className="font-data-lg text-headline-md text-primary">
            {s.faultType || 'NONE'}
          </div>
        </div>

        <div className="glass-card p-3 text-center">
          <div className="font-label-caps text-label-caps text-on-surface-variant">
            STATUS
          </div>
          <div className="font-data-lg text-headline-md text-secondary">
            {s.status || '--'}
          </div>
        </div>

        <div className="glass-card p-3 text-center">
          <div className="font-label-caps text-label-caps text-on-surface-variant">
            SCENARIO
          </div>
          <div className="font-data-lg text-headline-md text-primary">
            {s.scenario || 'NORMAL'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-gutter">
        <TimeSeriesChart
          data={chartData}
          dataKey="rpm"
          label="RPM"
          color="#00dbe9"
          padding={150}
        />

        <TimeSeriesChart
          data={chartData}
          dataKey="temperature"
          label="TEMPERATURE"
          color="#ffb95f"
          unit="°C"
          padding={5}
        />

        <TimeSeriesChart
          data={chartData}
          dataKey="vibration"
          label="VIBRATION"
          color="#ff8a80"
          unit=" mm/s"
          padding={1}
        />

        <TimeSeriesChart
          data={chartData}
          dataKey="pressure"
          label="PRESSURE"
          color="#4edea3"
          unit=" bar"
          padding={0.5}
        />

        <TimeSeriesChart
          data={chartData}
          dataKey="load"
          label="LOAD"
          color="#dbfcff"
          unit="%"
          padding={8}
        />

        <TimeSeriesChart
          data={chartData}
          dataKey="anomalyScore"
          label="ANOMALY SCORE"
          color="#fff3ea"
        />
      </div>

      <AlertFeed alerts={s.alerts} />

    </div>
  )
}