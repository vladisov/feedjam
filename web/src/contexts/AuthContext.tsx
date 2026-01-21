import { createContext, useContext, useState, useEffect, useMemo, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api, tokenStorage, AUTH_ERROR_EVENT } from '@/lib/api'
import type { AuthUser, LoginCredentials, RegisterCredentials } from '@/types/feed'

interface AuthContextType {
  user: AuthUser | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  register: (credentials: RegisterCredentials) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const queryClient = useQueryClient()

  // Check existing token on mount
  useEffect(() => {
    const token = tokenStorage.getAccessToken()
    if (!token) {
      setIsLoading(false)
      return
    }

    api.getMe()
      .then(setUser)
      .catch(() => tokenStorage.clearTokens())
      .finally(() => setIsLoading(false))
  }, [])

  // Listen for auth errors (expired session, etc.)
  useEffect(() => {
    const handleAuthError = () => setUser(null)
    window.addEventListener(AUTH_ERROR_EVENT, handleAuthError)
    return () => window.removeEventListener(AUTH_ERROR_EVENT, handleAuthError)
  }, [])

  const value = useMemo<AuthContextType>(() => ({
    user,
    isLoading,
    isAuthenticated: !!user,
    login: async (credentials) => {
      queryClient.clear()
      await api.login(credentials)
      setUser(await api.getMe())
    },
    register: async (credentials) => {
      queryClient.clear()
      await api.register(credentials)
      setUser(await api.getMe())
    },
    logout: () => {
      api.logout()
      setUser(null)
      queryClient.clear()
    },
    refreshUser: async () => {
      setUser(await api.getMe())
    },
  }), [user, isLoading, queryClient])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
