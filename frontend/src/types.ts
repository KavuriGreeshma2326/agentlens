export type Difficulty = 'easy' | 'medium' | 'hard'

export interface Task {
  id: number
  name: string
  description: string | null
  expected_output: string | null
  difficulty: Difficulty
  created_at: string | null
}

export type RunStatus = 'queued' | 'running' | 'passed' | 'failed'

export interface Run {
  id: number
  task_id: number
  status: RunStatus | null
  agent_version: string
  total_cost: number
  total_latency_ms: number
  created_at: string | null
  completed_at: string | null
}

export type StepType = 'thought' | 'tool_call' | 'tool_result' | 'final'

export interface RunStep {
  id: number
  step_number: number
  step_type: StepType
  content: string | null
  latency_ms: number
  tokens: number
}

/** Why a failed run failed, with the step numbers that prove it. */
export interface Diagnosis {
  label: string
  summary: string
  step_numbers: number[]
}

export interface RunDetail extends Run {
  steps: RunStep[]
  diagnosis: Diagnosis | null
}

export interface VersionStats {
  agent_version: string
  runs: number
  passed: number
  failed: number
  pass_rate: number
  avg_cost: number
  avg_latency_ms: number
  failure_counts: Record<string, number>
}

export interface Stats {
  total_runs: number
  versions: VersionStats[]
}