import { useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, login, register } from './api'

type Mode = 'login' | 'register'

interface AuthScreenProps {
  onAuthenticated: (token: string) => void
}

// Checked in the browser only. The backend does not enforce a minimum yet.
const MIN_PASSWORD_LENGTH = 8

export default function AuthScreen({ onAuthenticated }: AuthScreenProps) {
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const isRegister = mode === 'register'

  function switchMode() {
    setMode(isRegister ? 'login' : 'register')
    setError(null)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (isRegister && password.length < MIN_PASSWORD_LENGTH) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`)
      return
    }

    setSubmitting(true)
    try {
      const result = isRegister
        ? await register(email, password)
        : await login(email, password)
      onAuthenticated(result.access_token)
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
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center p-6">
      <header className="mb-10 text-center select-none">
        <h1 className="text-5xl font-black tracking-tight text-white">
          Agent<span className="text-indigo-400">Lens</span>
        </h1>
        <p className="mt-2 text-sm text-gray-500 tracking-widest uppercase">
          AI Agent Evaluation Platform
        </p>
      </header>

      <main className="w-full max-w-sm">
        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-2xl border border-gray-800 bg-gray-900 p-6 shadow-2xl"
        >
          <h2 className="text-lg font-semibold text-white">
            {isRegister ? 'Create your account' : 'Sign in'}
          </h2>

          <div>
            <label
              htmlFor="email"
              className="mb-1 block text-xs font-semibold uppercase tracking-widest text-gray-500"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-100 focus:border-indigo-400 focus:outline-none"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-1 block text-xs font-semibold uppercase tracking-widest text-gray-500"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-100 focus:border-indigo-400 focus:outline-none"
            />
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
            {submitting
              ? 'Please wait...'
              : isRegister
                ? 'Create account'
                : 'Sign in'}
          </button>

          <p className="text-center text-xs text-gray-500">
            {isRegister ? 'Already have an account?' : 'New here?'}{' '}
            <button
              type="button"
              onClick={switchMode}
              className="text-indigo-400 hover:underline"
            >
              {isRegister ? 'Sign in' : 'Create an account'}
            </button>
          </p>
        </form>
      </main>
    </div>
  )
}