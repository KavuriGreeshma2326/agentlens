import { useCallback, useEffect, useState } from 'react'
import { ApiError } from './api'
import { getRun, getTask } from './endpoints'
import { labelInfo } from './failureLabels'
import { formatCost, formatLatency, formatTime } from './format'
import StatusPill from './StatusPill'
import type { RunDetail, StepType, Task } from './types'

const STEP_STYLES: Record<StepType, { label: string; badge: string }> = {
  thought: { label: 'Thought', badge: 'bg-sky-400/10 text-sky-400' },
  tool_call: { label: 'Tool call', badge: 'bg-violet-400/10 text-violet-400' },
  tool_result: {
    label: 'Tool result',
    badge: 'bg-amber-400/10 text-amber-400',
  },
  final: { label: 'Final answer', badge: 'bg-emerald-400/10 text-emerald-400' },
}

const labelClass =
  'text-xs font-semibold uppercase tracking-widest text-gray-500'

function messageOf(err: unknown): string {
  return err instanceof ApiError
    ? err.message
    : 'Something went wrong. Please try again.'
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-widest text-gray-500">
        {label}
      </dt>
      <dd className="mt-1 text-sm font-medium text-gray-100">{value}</dd>
    </div>
  )
}

export default function RunDetailPage({ runId }: { runId: number }) {
  const [run, setRun] = useState<RunDetail | null>(null)
  const [task, setTask] = useState<Task | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setRun(await getRun(runId))
      setError(null)
    } catch (err: unknown) {
      setError(messageOf(err))
    }
  }, [runId])

  useEffect(() => {
    void load()
  }, [load])

  // While the run is unfinished, check again every second.
  useEffect(() => {
    if (!run || (run.status !== 'queued' && run.status !== 'running')) return
    const timer = setTimeout(() => void load(), 1000)
    return () => clearTimeout(timer)
  }, [run, load])

  // Load the task once its id is known, to show its name and expected output.
  const taskId = run?.task_id
  useEffect(() => {
    if (taskId === undefined) return
    let cancelled = false
    getTask(taskId)
      .then((loaded) => {
        if (!cancelled) setTask(loaded)
      })
      .catch(() => {
        // The trace is still useful without the task details.
      })
    return () => {
      cancelled = true
    }
  }, [taskId])

  const steps = run?.steps ?? []
  const totalTokens = steps.reduce((sum, step) => sum + step.tokens, 0)
  const maxLatency = Math.max(1, ...steps.map((step) => step.latency_ms))
  const lastStep = steps.length > 0 ? steps[steps.length - 1] : null
  const finalAnswer =
    lastStep !== null && lastStep.step_type === 'final'
      ? lastStep.content
      : null
  const expected = task?.expected_output ?? null
  const finished = run?.status === 'passed' || run?.status === 'failed'

  // Steps the diagnosis points at as evidence.
  const evidence = new Set(run?.diagnosis?.step_numbers ?? [])
  const diagnosisInfo = run?.diagnosis ? labelInfo(run.diagnosis.label) : null

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <a href="#/" className="inline-block text-sm text-indigo-400 hover:underline">
        Back to tasks
      </a>

      {error && (
        <p
          role="alert"
          className="rounded-lg border border-red-900 bg-red-950 px-4 py-3 text-sm text-red-300"
        >
          {error}
        </p>
      )}

      {run === null && error === null && (
        <p className="text-sm text-gray-500">Loading...</p>
      )}

      {run !== null && (
        <>
          <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0">
                <p className={labelClass}>Run #{run.id}</p>
                <h2 className="mt-1 truncate text-xl font-semibold text-white">
                  {task ? task.name : `Task ${run.task_id}`}
                </h2>
                <p className="mt-1 text-xs text-gray-500">
                  Started {formatTime(run.created_at)}
                </p>
              </div>
              <StatusPill status={run.status} />
            </div>

            <dl className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-5">
              <Stat label="Agent version" value={run.agent_version} />
              <Stat label="Steps" value={String(steps.length)} />
              <Stat label="Tokens" value={String(totalTokens)} />
              <Stat label="Latency" value={formatLatency(run.total_latency_ms)} />
              <Stat label="Cost" value={formatCost(run.total_cost)} />
            </dl>
          </div>

          {run.diagnosis && diagnosisInfo && (
            <div className="rounded-2xl border border-red-900/60 bg-red-950/20 p-6">
              <div className="flex flex-wrap items-center gap-3">
                <p className={labelClass}>Failure autopsy</p>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${diagnosisInfo.badge}`}
                >
                  {diagnosisInfo.title}
                </span>
              </div>
              <p className="mt-3 text-sm text-gray-200">
                {run.diagnosis.summary}
              </p>
              {run.diagnosis.step_numbers.length > 0 && (
                <p className="mt-2 text-xs text-gray-500">
                  Evidence:{' '}
                  {run.diagnosis.step_numbers.length === 1 ? 'step' : 'steps'}{' '}
                  {run.diagnosis.step_numbers.join(', ')}. Highlighted in the
                  trace below.
                </p>
              )}
            </div>
          )}

          {finished && (
            <div className="grid gap-4 rounded-2xl border border-gray-800 bg-gray-900 p-6 sm:grid-cols-2">
              <div>
                <p className={labelClass}>Expected output</p>
                <p className="mt-1 text-sm text-gray-100">
                  {expected ?? 'None set for this task'}
                </p>
              </div>
              <div>
                <p className={labelClass}>Final answer</p>
                <p className="mt-1 text-sm text-gray-100">
                  {finalAnswer ?? 'No final answer'}
                </p>
              </div>
              {expected !== null && finalAnswer !== null && (
                <p
                  className={`text-xs sm:col-span-2 ${
                    finalAnswer === expected ? 'text-emerald-400' : 'text-red-400'
                  }`}
                >
                  {finalAnswer === expected
                    ? 'Exact match'
                    : 'Does not match the expected output'}
                </p>
              )}
            </div>
          )}

          <div className="rounded-2xl border border-gray-800 bg-gray-900">
            <div className="border-b border-gray-800 px-6 py-4">
              <h3 className={labelClass}>Trace</h3>
            </div>

            {steps.length === 0 ? (
              <p className="px-6 py-6 text-sm text-gray-500">
                No steps recorded yet.
              </p>
            ) : (
              <ol className="divide-y divide-gray-800">
                {steps.map((step) => {
                  const style = STEP_STYLES[step.step_type]
                  const isError = step.content?.startsWith('Error:') ?? false
                  const isEvidence = evidence.has(step.step_number)
                  return (
                    <li
                      key={step.id}
                      className={`px-6 py-4 ${
                        isEvidence ? 'border-l-2 border-red-500 bg-red-500/5' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                          <span className="w-6 text-xs text-gray-600">
                            {step.step_number}
                          </span>
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${style.badge}`}
                          >
                            {style.label}
                          </span>
                          {isEvidence && (
                            <span className="text-xs font-medium text-red-400">
                              evidence
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-gray-500">
                          {step.latency_ms} ms - {step.tokens} tokens
                        </span>
                      </div>

                      <p
                        className={`mt-2 whitespace-pre-wrap break-words pl-9 font-mono text-sm ${
                          isError ? 'text-red-400' : 'text-gray-300'
                        }`}
                      >
                        {step.content}
                      </p>

                      <div className="mt-3 pl-9">
                        <div className="h-1 rounded-full bg-gray-800">
                          <div
                            className="h-1 rounded-full bg-indigo-500/70"
                            style={{
                              width: `${(step.latency_ms / maxLatency) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    </li>
                  )
                })}
              </ol>
            )}
          </div>
        </>
      )}
    </div>
  )
}