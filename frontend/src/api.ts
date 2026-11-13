// VITE_API_URL is injected at build/dev time from the environment.
// Falls back to localhost:8000 so `npm run dev` works without a .env file.
export const API_URL: string =
  import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const TOKEN_KEY = 'agentlens_token'

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

  let res: Response
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers })
  } catch {
    throw new ApiError(0, 'Could not reach the server. Is the backend running?')
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