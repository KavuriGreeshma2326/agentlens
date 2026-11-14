import { useCallback, useEffect, useState } from 'react'
import type { ReactElement } from 'react'
import AuthScreen from './AuthScreen'
import DashboardPage from './DashboardPage'
import RunDetailPage from './RunDetailPage'
import TasksPage from './TasksPage'
import { ApiError, clearToken, getCurrentUser, getToken, setToken } from './api'
import type { User } from './api'
import { useHash } from './useHash'

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

  return <SignedInLayout email={session.user.email} onLogout={handleLogout} />
}

function navClass(active: boolean): string {
  return active
    ? 'font-medium text-white'
    : 'text-gray-400 hover:text-gray-200'
}

function SignedInLayout({
  email,
  onLogout,
}: {
  email: string
  onLogout: () => void
}) {
  // Routes use the URL hash (for example "#/runs/5" or "#/dashboard"). The
  // hash is never sent to the server, so this works on static hosting
  // without extra setup.
  const hash = useHash()
  const match = /^#\/runs\/(\d+)$/.exec(hash)
  const runId = match ? Number(match[1]) : null
  const onDashboard = hash === '#/dashboard'

  let page: ReactElement
  if (runId !== null) {
    page = <RunDetailPage key={runId} runId={runId} />
  } else if (onDashboard) {
    page = <DashboardPage />
  } else {
    page = <TasksPage />
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-800 px-6 py-4">
        <div className="flex items-center gap-8">
          <h1 className="text-xl font-black tracking-tight text-white">
            <a href="#/">
              Agent<span className="text-indigo-400">Lens</span>
            </a>
          </h1>
          <nav className="flex items-center gap-6 text-sm">
            <a href="#/" className={navClass(!onDashboard)}>
              Tasks
            </a>
            <a href="#/dashboard" className={navClass(onDashboard)}>
              Dashboard
            </a>
          </nav>
        </div>
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

      <main>{page}</main>
    </div>
  )
}