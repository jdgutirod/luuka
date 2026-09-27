import { useState } from 'react'
import { getErrorMessage } from '../../api/errors'
import { Alert } from '../../components/Alert'
import { Avatar } from '../../components/Avatar'
import { Button } from '../../components/Button'
import { CheckIcon, CopyIcon, LogOutIcon } from '../../components/icons'
import { PageHeader } from '../../components/PageHeader'
import { formatLongDate } from '../../lib/date'
import { formatPlate } from '../../lib/plate'
import { useAuth } from '../auth/useAuth'
import { useMyAccount } from './api'

// The clipboard API only exists on https or localhost
const canCopy = typeof navigator !== 'undefined' && navigator.clipboard !== undefined

export function ProfilePage() {
  const { logout } = useAuth()
  const { data: account, isPending, error, refetch } = useMyAccount()
  const [copied, setCopied] = useState(false)

  const copyPlate = async (plate: string) => {
    try {
      await navigator.clipboard.writeText(formatPlate(plate))
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Permission denied: the plate is still visible to copy by hand
    }
  }

  return (
    <>
      <PageHeader title="Perfil" />

      {isPending && <p className="text-slate-500">Cargando tu cuenta…</p>}
      {error && (
        <Alert onRetry={() => refetch()}>
          <p>{getErrorMessage(error)}</p>
        </Alert>
      )}

      {account && (
        <div className="flex flex-col gap-4">
          <section className="flex flex-col items-center rounded-3xl bg-white p-6 text-center ring-1 ring-slate-200">
            <Avatar name={account.owner_name} size="lg" />
            <h2 className="mt-3 text-lg font-semibold text-slate-900">{account.owner_name}</h2>
            <p className="text-sm text-slate-500">{account.email}</p>
            <p className="mt-1 text-xs text-slate-400">En Luuka desde el {formatLongDate(account.created_at)}</p>
          </section>

          <section className="rounded-3xl bg-white p-6 ring-1 ring-slate-200">
            <p className="text-sm font-medium text-slate-500">Tu placa</p>
            <div className="mt-2 flex items-center justify-between gap-3">
              <span className="rounded-lg border-2 border-slate-900 bg-yellow-300 px-3 py-1 font-mono text-2xl font-bold tracking-wider text-slate-900">
                {formatPlate(account.plate)}
              </span>
              {canCopy && (
                <Button variant="ghost" onClick={() => copyPlate(account.plate)}>
                  {copied ? <CheckIcon className="size-4" /> : <CopyIcon className="size-4" />}
                  {copied ? 'Copiada' : 'Copiar'}
                </Button>
              )}
            </div>
            <p className="mt-3 text-sm text-slate-500">
              Compártela para que te transfieran dinero o te agreguen a un cobro de cancha.
            </p>
          </section>
        </div>
      )}

      <Button variant="danger" className="mt-6 w-full" onClick={logout}>
        <LogOutIcon className="size-4" />
        Cerrar sesión
      </Button>
    </>
  )
}
