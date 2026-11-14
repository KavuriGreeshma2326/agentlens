import { useEffect, useState } from 'react'
import { ApiError } from './api'
import { getStats } from './endpoints'
import { MAIN_FAILURE_LABELS, labelInfo } from './failureLabels'
import { formatCost, formatLatency } from './format'
import type { Stats, VersionStats } from './types'

// Below this many finished runs per version, differences may just be noise.
const SMALL_SAMPLE = 20

const labelClass =
  'text-xs font-semibold uppercase tracking-widest text-gray-500'

function messageOf(err: unknown): string {
  return err instanceof ApiError
    ? err.message
    : 'Something went wrong. Please try again.'
}

function leaderText(versions: VersionStats[]): string | null {
  if (versions.length < 2) return null
  const sorted = [...versions].sort((a, b) => b.pass_rate - a.pass_rate)
  const best = sorted[0]
  const worst = sorted[sorted.length - 1]
  const points = Math.round((best.pass_rate - worst.pass_rate) * 100)
  if (points === 0) return 'All versions pass at the same rate.'
  return `${best.agent_version} passes ${points} percentage points more often than ${worst.agent_version}.`
}

function VersionCard({ stats }: { stats: VersionStats }) {
  const percent = Math.round(stats.pass_rate * 100)
  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6">
      <p className={labelClass}>{stats.agent_version}</p>
      <p className="mt-2 text-4xl font-black text-white">{percent}%</p>
      <p className="mt-1 text-xs text-gray-500">
        pass rate - {stats.passed} passed, {stats.failed} failed of {stats.runs}{' '}
        runs
      </p>

      <div className="mt-4 h-2 rounded-full bg-gray-800">
        <div
          className="h-2 rounded-full bg-emerald-500"
          style={{ width: `${percent}%` }}
        />
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-4">
        <div>
          <dt className="text-xs uppercase tracking-widest text-gray-500">
            Avg cost
          </dt>
          <dd className="mt-1 text-sm font-medium text-gray-100">
            {formatCost(stats.avg_cost)}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-widest text-gray-500">
            Avg latency
          </dt>
          <dd className="mt-1 text-sm font-medium text-gray-100">
            {formatLatency(stats.avg_latency_ms)}
          </dd>
        </div>
      </dl>
    </div>
  )
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        setStats(await getStats())
      } catch (err: unknown) {
        setError(messageOf(err))
      }
    }
    void load()
  }, [])

  // The four main causes first, then any extra label that actually occurred.
  const labels = [...MAIN_FAILURE_LABELS]
  for (const version of stats?.versions ?? []) {
    for (const key of Object.keys(version.failure_counts)) {
      if (!labels.includes(key)) labels.push(key)
    }
  }
  const maxCount = Math.max(
    1,
    ...(stats?.versions ?? []).flatMap((v) => Object.values(v.failure_counts)),
  )

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div>
        <h2 className="text-xl font-semibold text-white">Dashboard</h2>
        <p className="mt-1 text-sm text-gray-500">
          Finished runs, compared by agent version.
        </p>
      </div>

      {error && (
        <p
          role="alert"
          className="rounded-lg border border-red-900 bg-red-950 px-4 py-3 text-sm text-red-300"
        >
          {error}
        </p>
      )}

      {stats === null && error === null && (
        <p className="text-sm text-gray-500">Loading...</p>
      )}

      {stats !== null && stats.total_runs === 0 && (
        <p className="rounded-2xl border border-gray-800 bg-gray-900 px-6 py-6 text-sm text-gray-500">
          No finished runs yet. Start some runs on the Tasks page.
        </p>
      )}

      {stats !== null && stats.total_runs > 0 && (
        <>
          {leaderText(stats.versions) && (
            <p className="text-sm text-gray-300">{leaderText(stats.versions)}</p>
          )}

          {stats.versions.some((v) => v.runs < SMALL_SAMPLE) && (
            <p className="text-xs text-amber-400">
              Small sample: at least one version has fewer than {SMALL_SAMPLE}{' '}
              finished runs, so differences may be noise.
            </p>
          )}

          <div className="grid gap-6 sm:grid-cols-2">
            {stats.versions.map((v) => (
              <VersionCard key={v.agent_version} stats={v} />
            ))}
          </div>

          <div className="rounded-2xl border border-gray-800 bg-gray-900">
            <div className="border-b border-gray-800 px-6 py-4">
              <h3 className={labelClass}>Why runs failed</h3>
            </div>
            <ul className="divide-y divide-gray-800">
              {labels.map((label) => {
                const info = labelInfo(label)
                return (
                  <li key={label} className="px-6 py-4">
                    <div className="flex flex-wrap items-baseline justify-between gap-4">
                      <p className="text-sm font-medium text-gray-100">
                        {info.title}
                      </p>
                      <p className="text-xs text-gray-500">{info.description}</p>
                    </div>
                    <div className="mt-3 space-y-2">
                      {stats.versions.map((v) => {
                        const count = v.failure_counts[label] ?? 0
                        return (
                          <div
                            key={v.agent_version}
                            className="flex items-center gap-3"
                          >
                            <span className="w-20 shrink-0 text-xs text-gray-500">
                              {v.agent_version}
                            </span>
                            <div className="h-2 flex-1 rounded-full bg-gray-800">
                              <div
                                className="h-2 rounded-full bg-red-400/70"
                                style={{ width: `${(count / maxCount) * 100}%` }}
                              />
                            </div>
                            <span className="w-6 text-right text-xs text-gray-400">
                              {count}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </li>
                )
              })}
            </ul>
          </div>
        </>
      )}
    </div>
  )
}