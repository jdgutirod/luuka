// The access token is kept in localStorage so the session survives a page reload.
// Simple for the MVP, but readable by any script running on the page (XSS): an httpOnly cookie
// with a refresh token is the safer long-term option and needs changes in the backend.
const TOKEN_KEY = 'luuka.accessToken'

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function saveToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch {
    // Storage can be blocked (private mode); the session then lasts until the page is closed
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch {
    // Nothing to clear if storage is blocked
  }
}
