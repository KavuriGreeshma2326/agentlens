import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from './api'
import { createTask } from './endpoints'
import type { Difficulty, Task } from './types'

interface TaskFormProps {
  onCreated: (task: Task) => void
}

const labelClass =
  'mb-1 block text-xs font-semibold uppercase tracking-widest text-gray-500'
const inputClass =
  'w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-100 focus:border-indigo-400 focus:outline-none'

export default function TaskForm({ onCreated }: TaskFormProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [expectedOutput, setExpectedOutput] = useState('')
  const [difficulty, setDifficulty] = useState<Difficulty>('medium')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    const trimmedName = name.trim()
    if (!trimmedName) {
      setError('Give the task a name.')
      return
    }

    setSubmitting(true)
    try {
      const task = await createTask({
        name: trimmedName,
        description: description.trim() || null,
        expected_output: expectedOutput.trim() || null,
        difficulty,
      })
      onCreated(task)
      setName('')
      setDescription('')
      setExpectedOutput('')
      setDifficulty('medium')
    } catch (err: unknown) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Something went wrong. Please try again.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 rounded-2xl border border-gray-800 bg-gray-900 p-5"
    >
      <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-500">
        New task
      </h2>

      <div>
        <label htmlFor="task-name" className={labelClass}>
          Name
        </label>
        <input
          id="task-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className={inputClass}
        />
      </div>

      <div>
        <label htmlFor="task-description" className={labelClass}>
          Description
        </label>
        <textarea
          id="task-description"
          rows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className={inputClass}
        />
      </div>

      <div>
        <label htmlFor="task-expected" className={labelClass}>
          Expected output
        </label>
        <input
          id="task-expected"
          type="text"
          value={expectedOutput}
          onChange={(e) => setExpectedOutput(e.target.value)}
          className={inputClass}
        />
        <p className="mt-1 text-xs text-gray-600">
          What a correct final answer looks like. A passing run ends with it.
        </p>
      </div>

      <div>
        <label htmlFor="task-difficulty" className={labelClass}>
          Difficulty
        </label>
        <select
          id="task-difficulty"
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value as Difficulty)}
          className={inputClass}
        >
          <option value="easy">easy</option>
          <option value="medium">medium</option>
          <option value="hard">hard</option>
        </select>
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-400">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-lg bg-indigo-500 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-400 disabled:opacity-50"
      >
        {submitting ? 'Adding...' : 'Add task'}
      </button>
    </form>
  )
}