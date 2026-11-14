import type { RunStatus } from './types'

const STYLES: Record<RunStatus, string> = {
  queued: 'bg-gray-400/10 text-gray-400',
  running: 'bg-amber-400/10 text-amber-400 animate-pulse',
  passed: 'bg-emerald-400/10 text-emerald-400',
  failed: 'bg-red-400/10 text-red-400',
}

export default function StatusPill({ status }: { status: RunStatus | null }) {
  const key: RunStatus = status ?? 'queued'
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${STYLES[key]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {key}
    </span>
  )
}