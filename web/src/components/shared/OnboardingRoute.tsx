import { Navigate } from 'react-router-dom'

import { useAuth } from '@/contexts/AuthContext'

import { PageLoader } from './LoadingSpinner'

interface OnboardingRouteProps {
  children: React.ReactNode
}

export function OnboardingRoute({ children }: OnboardingRouteProps): React.ReactNode {
  const { user, isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <PageLoader />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (user?.onboarding_completed) {
    return <Navigate to="/" replace />
  }

  return children
}
