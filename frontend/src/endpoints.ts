import { apiRequest } from './api'
import type { Difficulty, Run, RunDetail, Task } from './types'

export interface NewTask {
  name: string
  description: string | null
  expected_output: string | null
  difficulty: Difficulty
}

export function listTasks(): Promise<Task[]> {
  return apiRequest<Task[]>('/tasks')
}

export function getTask(taskId: number): Promise<Task> {
  return apiRequest<Task>(`/tasks/${taskId}`)
}

export function createTask(task: NewTask): Promise<Task> {
  return apiRequest<Task>('/tasks', {
    method: 'POST',
    body: JSON.stringify(task),
  })
}

export function listRuns(): Promise<Run[]> {
  return apiRequest<Run[]>('/runs')
}

export function getRun(runId: number): Promise<RunDetail> {
  return apiRequest<RunDetail>(`/runs/${runId}`)
}

export function startRun(taskId: number, agentVersion: string): Promise<Run> {
  return apiRequest<Run>(`/tasks/${taskId}/runs`, {
    method: 'POST',
    body: JSON.stringify({ agent_version: agentVersion }),
  })
}