import { useEffect, useState } from 'react'

// VITE_API_URL is injected at build/dev time from the environment.
// Falls back to localhost:8000 so `npm run dev` works without a .env file.
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// ── Types ────────────────────────────────────────────────────────────────────

interface HealthResponse {
  status: string
  service: string
}

type HealthState =
  | { kind: 'loading' }
  | { kind: 'success'; data: HealthResponse }
  | { kind: 'error'; message: string }

// ── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [state, setState] = useState<HealthState>({ kind: 'loading' })

  useEffect(() => {
    setState({ kind: 'loading' })

    fetch(`${API_URL}/health`)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data: HealthResponse = await res.json()
        setState({ kind: 'success', data })
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : 'Unknown error'
        setState({ kind: 'error', message: msg })
      })
  }, [])

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center p-6">
      {/* Logo */}
      <header className="mb-10 text-center select-none">
        <h1 className="text-5xl font-black tracking-tight text-white">
          Agent<span className="text-indigo-400">Lens</span>
        </h1>
        <p className="mt-2 text-sm text-gray-500 tracking-widest uppercase">
          AI Agent Evaluation Platform
        </p>
      </header>

      {/* Health card */}
      <main className="w-full max-w-sm">
        <div className="rounded-2xl border border-gray-800 bg-gray-900 shadow-2xl overflow-hidden">
          {/* Card header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
            <span className="text-xs font-semibold tracking-widest uppercase text-gray-500">
              Backend Health
            </span>
            <StatusPill state={state} />
          </div>

          {/* Card body */}
          <div className="px-5 py-5">
            <HealthBody state={state} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-8 text-xs text-gray-700">
        Day 1 — backend at{' '}
        <code className="text-indigo-500">{API_URL}</code>
      </footer>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StatusPill({ state }: { state: HealthState }) {
  if (state.kind === 'loading') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-400/10 px-3 py-1 text-xs font-medium text-amber-400 animate-pulse">
        <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
        Checking…
      </span>
    )
  }
  if (state.kind === 'success') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-400">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
        Online
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-red-400/10 px-3 py-1 text-xs font-medium text-red-400">
      <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
      Offline
    </span>
  )
}

function HealthBody({ state }: { state: HealthState }) {
  if (state.kind === 'loading') {
    return (
      <div className="space-y-3">
        <Skeleton width="75%" />
        <Skeleton width="50%" />
        <Skeleton width="60%" />
      </div>
    )
  }

  if (state.kind === 'success') {
    return (
      <dl className="space-y-3">
        <Row label="status" value={state.data.status} valueClass="text-emerald-400 font-semibold" />
        <Row label="service" value={state.data.service} />
        <Row
          label="endpoint"
          value={`${API_URL}/health`}
          valueClass="text-indigo-400 font-mono text-xs"
        />
      </dl>
    )
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-semibold text-red-400">Could not reach backend</p>
      <p className="text-xs text-gray-500">{state.message}</p>
      <p className="text-xs text-gray-600 pt-1">
        Make sure the backend is running at{' '}
        <code className="text-indigo-500">{API_URL}</code>
      </p>
    </div>
  )
}

function Row({
  label,
  value,
  valueClass = 'text-gray-100',
}: {
  label: string
  value: string
  valueClass?: string
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <dt className="shrink-0 font-mono text-sm text-gray-500">{label}</dt>
      <dd className={`truncate text-sm text-right ${valueClass}`}>{value}</dd>
    </div>
  )
}

function Skeleton({ width }: { width: string }) {
  return (
    <div
      className="h-4 rounded-md bg-gray-800 animate-pulse"
      style={{ width }}
    />
  )
}
