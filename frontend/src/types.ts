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