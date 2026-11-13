import { useCallback, useEffect, useState } from 'react'
import AuthScreen from './AuthScreen'
import { ApiError, clearToken, getCurrentUser, getToken, setToken } from './api'
import type { User } from './api'

type Session =
  | { kind: 'checking' }
  | { kind: 'signed-out' }
  | { kind: 'signed-in'; user: User }

export default function App() {
  const [session, setSession] = useState<Session>({ kind: 'checking' })

  const loadSession = useCallback(async () => {
    if (!getToken()) {
      setSession({ kind: 'signed-out' })
      return
    }
    try {
      const user = await getCurrentUser()
      setSession({ kind: 'signed-in', user })
    } catch (err: unknown) {
      // An expired or invalid token is cleared. Other errors (such as the
      // server being down) leave the token alone so a refresh can recover.
      if (err instanceof ApiError && err.status === 401) clearToken()
      setSession({ kind: 'signed-out' })
    }
  }, [])

  useEffect(() => {
    void loadSession()
  }, [loadSession])

  function handleAuthenticated(token: string) {
    setToken(token)
    setSession({ kind: 'checking' })
    void loadSession()
  }

  function handleLogout() {
    clearToken()
    setSession({ kind: 'signed-out' })
  }

  if (session.kind === 'checking') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-950 text-sm text-gray-500">
        Loading...
      </div>
    )
  }

  if (session.kind === 'signed-out') {
    return <AuthScreen onAuthenticated={handleAuthenticated} />
  }

  return <SignedInPlaceholder email={session.user.email} onLogout={handleLogout} />
}

function SignedInPlaceholder({
  email,
  onLogout,
}: {
  email: string
  onLogout: () => void
}) {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
        <h1 className="text-xl font-black tracking-tight text-white">
          Agent<span className="text-indigo-400">Lens</span>
        </h1>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-gray-400">{email}</span>
          <button
            type="button"
            onClick={onLogout}
            className="rounded-lg border border-gray-700 px-3 py-1.5 text-gray-300 hover:bg-gray-800"
          >
            Log out
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-3xl p-6">
        <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6">
          <p className="text-sm text-gray-300">
            You are signed in. Tasks and runs arrive in the next step.
          </p>
        </div>
      </main>
    </div>
  )
}