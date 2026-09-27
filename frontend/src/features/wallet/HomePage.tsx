import type { ComponentType } from 'react'
import { Link } from 'react-router'
import { getErrorMessage } from '../../api/errors'
import { Alert } from '../../components/Alert'
import { Avatar } from '../../components/Avatar'
import { EmptyState } from '../../components/EmptyState'
import { ChevronRightIcon, SendIcon, UsersIcon, WalletIcon } from '../../components/icons'
import { ListSkeleton } from '../../components/ListSkeleton'
import { formatCOP } from '../../lib/money'
import { formatPlate } from '../../lib/plate'
import { useMyAccount } from '../accounts/api'
import { useMyMemberCharges } from '../group-charges/api'
import { useRecentTransactions } from './api'
import { TransactionList } from './TransactionList'

const RECENT_LIMIT = 5

const quickActions = [
  { to: '/reload', label: 'Recargar', icon: WalletIcon },
  { to: '/transfer', label: 'Transferir', icon: SendIcon },
  { to: '/charges/new', label: 'Dividir cancha', icon: UsersIcon },
]

function QuickAction({ to, label, icon: Icon }: { to: string; label: string; icon: ComponentType<{ className?: string }> }) {
  return (
    <Link to={to} className="flex flex-col items-center gap-2 rounded-2xl bg-white p-3 ring-1 ring-slate-200 hover:bg-slate-50">
      <span className="flex size-11 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
        <Icon />
      </span>
      <span className="text-sm font-medium text-slate-700">{label}</span>
    </Link>
  )
}

function PendingChargesBanner() {
  const { data: pending } = useMyMemberCharges('PENDING')
  if (!pending || pending.length === 0) {
    return null
  }

  const total = pending.reduce((sum, charge) => sum + charge.assigned_amount, 0)
  return (
    <Link to="/charges" className="flex items-center gap-3 rounded-2xl bg-amber-50 p-4 ring-1 ring-amber-200 hover:bg-amber-100">
      <span className="flex size-10 items-center justify-center rounded-full bg-amber-200 font-bold text-amber-900">
        {pending.length}
      </span>
      <span className="flex-1">
        <span className="block font-semibold text-amber-900">
          {pending.length === 1 ? 'Tienes un cobro por pagar' : `Tienes ${pending.length} cobros por pagar`}
        </span>
        <span className="block text-sm text-amber-800">Total: {formatCOP(total)}</span>
      </span>
      <ChevronRightIcon className="size-5 text-amber-700" />
    </Link>
  )
}

function RecentTransactions({ myAccountId }: { myAccountId: string }) {
  const { data: transactions, isPending, error, refetch } = useRecentTransactions(RECENT_LIMIT)

  return (
    <section>
      <div className="mb-2 flex items-center justify-between px-1">
        <h2 className="font-semibold text-slate-900">Últimos movimientos</h2>
        <Link to="/transactions" className="text-sm font-semibold text-emerald-700 hover:underline">
          Ver todos
        </Link>
      </div>
      {isPending && <ListSkeleton rows={3} />}
      {error && (
        <Alert onRetry={() => refetch()}>
          <p>{getErrorMessage(error)}</p>
        </Alert>
      )}
      {transactions?.length === 0 && (
        <EmptyState title="Aún no tienes movimientos" description="Recarga saldo para empezar a usar tu billetera." />
      )}
      {transactions && transactions.length > 0 && (
        <TransactionList transactions={transactions} myAccountId={myAccountId} />
      )}
    </section>
  )
}

export function HomePage() {
  const { data: account, isPending, error, refetch } = useMyAccount()

  if (isPending) {
    return <ListSkeleton rows={4} />
  }
  if (error) {
    return (
      <Alert onRetry={() => refetch()}>
        <p>{getErrorMessage(error)}</p>
      </Alert>
    )
  }

  const firstName = account.owner_name.trim().split(/\s+/)[0]

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-500">Hola,</p>
          <h1 className="text-2xl font-semibold text-slate-900">{firstName}</h1>
        </div>
        <Link to="/profile" aria-label="Ir a tu perfil">
          <Avatar name={account.owner_name} />
        </Link>
      </header>

      <section className="rounded-3xl bg-linear-to-br from-emerald-600 to-emerald-800 p-6 text-white shadow-lg shadow-emerald-900/20">
        <p className="text-sm text-emerald-100">Saldo disponible</p>
        <p className="mt-1 text-4xl font-bold tabular-nums">{formatCOP(account.balance)}</p>
        <p className="mt-4 inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-sm">
          Tu placa
          <span className="font-mono font-semibold tracking-wide">{formatPlate(account.plate)}</span>
        </p>
      </section>

      <nav aria-label="Acciones rápidas" className="grid grid-cols-3 gap-3">
        {quickActions.map((action) => (
          <QuickAction key={action.to} {...action} />
        ))}
      </nav>

      <PendingChargesBanner />

      <RecentTransactions myAccountId={account.id} />
    </div>
  )
}
