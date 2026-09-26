import { api, unwrap } from '../../api/client'
import type { AccountCreate, AccountResponse } from '../../api/types'

/** Logs in and returns the access token. The backend expects a form (OAuth2), not JSON. */
export async function requestToken(email: string, password: string): Promise<string> {
  const { access_token } = await unwrap(
    api.POST('/accounts/login', {
      body: { username: email, password, scope: '' },
      bodySerializer: (body) => new URLSearchParams({ username: body.username, password: body.password }),
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  )
  return access_token
}

export function registerAccount(data: AccountCreate): Promise<AccountResponse> {
  return unwrap(api.POST('/accounts', { body: data }))
}
