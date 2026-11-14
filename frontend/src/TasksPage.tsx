import { useCallback, useEffect, useState } from 'react'
import { ApiError } from './api'
import { listRuns, listTasks, startRun } from './endpoints'
import { formatCost, formatLatency, formatTime } from './format'
import StatusPill from './StatusPill'
import TaskForm from './TaskForm'
import type { Run, Task } from './types'

const AGENT_VERSIONS = ['mock-v1', 'mock-v2']

function messageOf(err: unknown): string {
  return err instanceof ApiError
    ? err.message
    : 'Something went wrong. Please try again.'
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [version, setVersion] = useState(AGENT_VERSIONS[0])
  const [startingId, setStartingId] = useState<number | null>(null)

  const refreshRuns = useCallback(async () => {
    try {
      setRuns(await listRuns())
    } catch (err: unknown) {
      setError(messageOf(err))
    }
  }, [])

  // Load tasks and runs once, when the page first appears.
  useEffect(() => {
    async function load() {
      try {
        const [loadedTasks, loadedRuns] = await Promise.all([
          listTasks(),
          listRuns(),
        ])
        setTasks(loadedTasks)
        setRuns(loadedRuns)
      } catch (err: unknown) {
        setError(messageOf(err))
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [])

  // While any run is still queued or running, check again every second.
  useEffect(() => {
    if (
      !runs.some((run) => run.status === 'queued' || run.status === 'running')
    ) {
      return
    }
    const timer = setTimeout(() => void refreshRuns(), 1000)
    return () => clearTimeout(timer)
  }, [runs, refreshRuns])

  async function handleStart(taskId: number) {
    setError(null)
    setStartingId(taskId)
    try {
      await startRun(taskId, version)
      await refreshRuns()
    } catch (err: unknown) {
      setError(messageOf(err))
    } finally {
      setStartingId(null)
    }
  }

  function handleCreated(task: Task) {
    setTasks((previous) => [...previous, task])
  }

  const taskNames = new Map(tasks.map((t): [number, string] => [t.id, t.name]))

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      {error && (
        <p
          role="alert"
          className="rounded-lg border border-red-900 bg-red-950 px-4 py-3 text-sm text-red-300"
        >
          {error}
        </p>
      )}

      {loading ? (
        <p className="text-sm text-gray-500">Loading...</p>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="space-y-6">
            <TaskForm onCreated={handleCreated} />

            <div className="rounded-2xl border border-gray-800 bg-gray-900">
              <div className="flex items-center justify-between border-b border-gray-800 px-5 py-4">
                <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-500">
                  Tasks
                </h2>
                <label className="flex items-center gap-2 text-xs text-gray-500">
                  Agent version
                  <select
                    value={version}
                    onChange={(e) => setVersion(e.target.value)}
                    className="rounded-md border border-gray-700 bg-gray-950 px-2 py-1 text-xs text-gray-100"
                  >
                    {AGENT_VERSIONS.map((v) => (
                      <option key={v} value={v}>
                        {v}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              {tasks.length === 0 ? (
                <p className="px-5 py-6 text-sm text-gray-500">
                  No tasks yet. Add one above.
                </p>
              ) : (
                <ul className="divide-y divide-gray-800">
                  {tasks.map((task) => (
                    <li
                      key={task.id}
                      className="flex items-start justify-between gap-4 px-5 py-4"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-gray-100">
                          {task.name}
                        </p>
                        <p className="mt-0.5 truncate text-xs text-gray-500">
                          {task.difficulty}
                          {task.description ? ` - ${task.description}` : ''}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => void handleStart(task.id)}
                        disabled={startingId === task.id}
                        className="shrink-0 rounded-lg bg-indigo-500 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-400 disabled:opacity-50"
                      >
                        {startingId === task.id ? 'Starting...' : 'Run'}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>

          <section>
            <div className="rounded-2xl border border-gray-800 bg-gray-900">
              <div className="border-b border-gray-800 px-5 py-4">
                <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-500">
                  Runs
                </h2>
              </div>

              {runs.length === 0 ? (
                <p className="px-5 py-6 text-sm text-gray-500">
                  No runs yet. Click Run on a task.
                </p>
              ) : (
                <ul className="divide-y divide-gray-800">
                  {runs.map((run) => (
                    <li
                      key={run.id}
                      className="flex items-center justify-between gap-4 px-5 py-4"
                    >
                      <div className="min-w-0">
                        <a
                          href={`#/runs/${run.id}`}
                          className="block truncate text-sm text-gray-100 hover:text-indigo-300 hover:underline"
                        >
                          #{run.id}{' '}
                          {taskNames.get(run.task_id) ?? `Task ${run.task_id}`}
                        </a>
                        <p className="mt-0.5 text-xs text-gray-500">
                          {run.agent_version} - {formatCost(run.total_cost)} -{' '}
                          {formatLatency(run.total_latency_ms)} -{' '}
                          {formatTime(run.created_at)}
                        </p>
                      </div>
                      <StatusPill status={run.status} />
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  )
}