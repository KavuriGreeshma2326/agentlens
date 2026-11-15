// VITE_API_URL is injected at build/dev time from the environment.
// Falls back to localhost:8000 so `npm run dev` works without a .env file.
export const API_URL: string =
  import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const TOKEN_KEY = 'agentlens_token'

/** A request that takes longer than this is reported as "slow". */
const SLOW_REQUEST_MS = 3000

/** Fired on the window when the server rejects a saved token (HTTP 401). */
export const UNAUTHORIZED_EVENT = 'agentlens:unauthorized'

export interface User {
  email: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

/** An error response from the backend, or a failure to reach it (status 0). */
export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// -- Token storage ------------------------------------------------------------
// localStorage can be unavailable (private mode, blocked storage), so every
// access is wrapped. If storage fails, the user simply has to sign in again.

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch {
    // Storage unavailable: the session will not survive a page reload.
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch {
    // Nothing to clear if storage is unavailable.
  }
}

// -- Slow request tracking ----------------------------------------------------
// A free host goes to sleep when idle and can take up to a minute to wake.
// The UI subscribes here so it can say what is happening instead of showing
// a blank screen.

type SlowListener = (slow: boolean) => void

const slowListeners = new Set<SlowListener>()
let slowCount = 0

function notifySlow(): void {
  for (const listener of slowListeners) listener(slowCount > 0)
}

/** Call `listener` whenever "a request is taking unusually long" changes. */
export function subscribeSlow(listener: SlowListener): () => void {
  slowListeners.add(listener)
  listener(slowCount > 0)
  return () => {
    slowListeners.delete(listener)
  }
}

// -- Requests -----------------------------------------------------------------

async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail) && typeof body.detail[0]?.msg === 'string') {
      return body.detail[0].msg
    }
  } catch {
    // The body was not JSON; fall through to the generic message.
  }
  return `Request failed (HTTP ${res.status})`
}

/** Call the backend. Sends the saved token, if there is one. */
export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body !== undefined) headers.set('Content-Type', 'application/json')
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  // If the server takes a while to answer, tell the UI.
  const timing = { reportedSlow: false }
  const slowTimer = setTimeout(() => {
    timing.reportedSlow = true
    slowCount += 1
    notifySlow()
  }, SLOW_REQUEST_MS)

  let res: Response
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers })
  } catch {
    throw new ApiError(0, 'Could not reach the server. Is the backend running?')
  } finally {
    clearTimeout(slowTimer)
    if (timing.reportedSlow) {
      slowCount -= 1
      notifySlow()
    }
  }

  if (res.status === 401 && token) {
    // The saved token was rejected (expired or invalid): sign the user out.
    clearToken()
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
  }

  if (!res.ok) throw new ApiError(res.status, await errorMessage(res))
  if (res.status === 204) return undefined as unknown as T
  return (await res.json()) as T
}

// -- Auth endpoints -----------------------------------------------------------

export function login(email: string, password: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function register(
  email: string,
  password: string,
): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function getCurrentUser(): Promise<User> {
  return apiRequest<User>('/auth/me')
}