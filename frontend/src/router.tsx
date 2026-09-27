import { createBrowserRouter, Navigate } from 'react-router'
import { AppLayout } from './components/AppLayout'
import { ProfilePage } from './features/accounts/ProfilePage'
import { LoginPage } from './features/auth/LoginPage'
import { RegisterPage } from './features/auth/RegisterPage'
import { RequireAuth } from './features/auth/RequireAuth'
import { ChargesPage } from './features/group-charges/ChargesPage'
import { CreateChargePage } from './features/group-charges/CreateChargePage'
import { GroupChargeDetailPage } from './features/group-charges/GroupChargeDetailPage'
import { HomePage } from './features/wallet/HomePage'
import { ReloadPage } from './features/wallet/ReloadPage'
import { TransactionsPage } from './features/wallet/TransactionsPage'
import { TransferPage } from './features/wallet/TransferPage'

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        // Main tabs, with the floating nav
        element: <AppLayout withNav />,
        children: [
          { path: '/', element: <HomePage /> },
          { path: '/transactions', element: <TransactionsPage /> },
          { path: '/charges', element: <ChargesPage /> },
          { path: '/profile', element: <ProfilePage /> },
        ],
      },
      {
        // Step-by-step screens, with a back arrow instead of the nav
        element: <AppLayout />,
        children: [
          { path: '/reload', element: <ReloadPage /> },
          { path: '/transfer', element: <TransferPage /> },
          { path: '/charges/new', element: <CreateChargePage /> },
          { path: '/charges/:id', element: <GroupChargeDetailPage /> },
        ],
      },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])
