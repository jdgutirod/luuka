import createClient, { type Middleware } from 'openapi-fetch'
import { ApiError, getErrorMessage } from './errors'
import type { paths } from './schema'
import { getToken } from './session'

let handleUnauthorized = () => {}

/** Registers what to do when the session is no longer valid (expired or invalid token). */
export function setUnauthorizedHandler(handler: () => void): void {
  handleUnauthorized = handler
}

const authMiddleware: Middleware = {
  onRequest({ request }) {
    const token = getToken()
    if (token) {
      request.headers.set('Authorization', `Bearer ${token}`)
    }
    return request
  },
  onResponse({ request, response }) {
    // A 401 on the login itself means wrong credentials, not an expired session
    const isLogin = new URL(request.url).pathname.endsWith('/accounts/login')
    if (response.status === 401 && !isLogin && getToken()) {
      handleUnauthorized()
    }
    return response
  },
}

export const api = createClient<paths>({ baseUrl: import.meta.env.VITE_API_URL })
api.use(authMiddleware)

/** Returns the response data, or throws an ApiError with a message ready to show to the user. */
export async function unwrap<T>(request: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
  const { data, error, response } = await request
  if (error !== undefined || data === undefined) {
    throw new ApiError(getErrorMessage(error), response.status)
  }
  return data
}
