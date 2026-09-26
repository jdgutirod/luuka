import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { setUnauthorizedHandler } from '../../api/client'
import { clearToken, getToken, saveToken } from '../../api/session'
import { requestToken } from './api'
import { AuthContext } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [token, setToken] = useState(getToken)

  const login = useCallback(async (email: string, password: string) => {
    const newToken = await requestToken(email, password)
    saveToken(newToken)
    setToken(newToken)
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setToken(null)
    // Do not leave the previous user's data cached for the next one
    queryClient.clear()
  }, [queryClient])

  // The token lasts 30 minutes and there is no refresh token: when the API rejects it, log out
  useEffect(() => {
    setUnauthorizedHandler(logout)
  }, [logout])

  const value = useMemo(() => ({ isAuthenticated: token !== null, login, logout }), [token, login, logout])

  return <AuthContext value={value}>{children}</AuthContext>
}
