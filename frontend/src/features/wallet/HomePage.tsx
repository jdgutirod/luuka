import { getErrorMessage } from '../../api/errors'
import { Button } from '../../components/Button'
import { formatCOP } from '../../lib/money'
import { formatPlate } from '../../lib/plate'
import { useAuth } from '../auth/useAuth'
import { useMyAccount } from './api'

export function HomePage() {
  const { logout } = useAuth()
  const { data: account, isPending, error, refetch } = useMyAccount()

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3">
          <span className="text-lg font-bold text-emerald-700">Lukas</span>
          <Button variant="secondary" onClick={logout}>
            Cerrar sesión
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-8">
        {isPending && <p className="text-slate-500">Cargando tu cuenta…</p>}

        {error && (
          <div role="alert" className="rounded-xl bg-red-50 p-4 text-red-700">
            <p>{getErrorMessage(error)}</p>
            <Button variant="secondary" className="mt-3" onClick={() => refetch()}>
              Reintentar
            </Button>
          </div>
        )}

        {account && (
          <>
            <h1 className="text-2xl font-semibold text-slate-900">Hola, {account.owner_name}</h1>
            <p className="mt-1 text-sm text-slate-500">
              Tu placa: <span className="font-mono font-semibold text-slate-700">{formatPlate(account.plate)}</span>
            </p>

            <section className="mt-6 rounded-2xl bg-emerald-700 p-6 text-white shadow-sm">
              <p className="text-sm text-emerald-100">Saldo disponible</p>
              <p className="mt-1 text-4xl font-bold tabular-nums">{formatCOP(account.balance)}</p>
            </section>
          </>
        )}
      </main>
    </div>
  )
}
