import { Link } from 'react-router'
import { ApiError, getErrorMessage } from '../../api/errors'
import type { AccountPublic } from '../../api/types'
import { Alert } from '../../components/Alert'
import { Button } from '../../components/Button'
import { CheckIcon } from '../../components/icons'
import { Sheet } from '../../components/Sheet'
import { formatCOP } from '../../lib/money'
import { formatPlate } from '../../lib/plate'
import { useMyAccount } from '../accounts/api'
import { usePayMemberCharge } from './api'

export type ChargeToPay = {
  memberChargeId: string
  amount: number
  groupName: string
  creator: AccountPublic
}

type PayChargeSheetProps = {
  charge: ChargeToPay | null
  onClose: () => void
}

/** Confirms the payment of the user's part of a group charge. The money goes to whoever paid the court. */
export function PayChargeSheet({ charge, onClose }: PayChargeSheetProps) {
  const { data: account } = useMyAccount()
  const pay = usePayMemberCharge()

  const close = () => {
    pay.reset()
    onClose()
  }

  const notEnoughBalance = account !== undefined && charge !== null && account.balance < charge.amount
  const insufficientFunds = pay.error instanceof ApiError && pay.error.status === 400

  return (
    <Sheet open={charge !== null} onClose={close} title={pay.isSuccess ? '¡Listo!' : 'Pagar mi parte'}>
      {charge && pay.isSuccess && (
        <div className="flex flex-col items-center text-center">
          <span className="flex size-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
            <CheckIcon className="size-7" />
          </span>
          <p className="mt-3 text-slate-600">
            Pagaste {formatCOP(charge.amount)} a {charge.creator.owner_name} por «{charge.groupName}».
          </p>
          <Button className="mt-6 w-full" onClick={close}>
            Entendido
          </Button>
        </div>
      )}

      {charge && !pay.isSuccess && (
        <div className="flex flex-col gap-4">
          <div className="rounded-2xl bg-slate-50 p-4 text-center">
            <p className="text-sm text-slate-500">{charge.groupName}</p>
            <p className="mt-1 text-3xl font-bold text-slate-900 tabular-nums">{formatCOP(charge.amount)}</p>
            <p className="mt-2 text-sm text-slate-500">
              Para {charge.creator.owner_name} · <span className="font-mono">{formatPlate(charge.creator.plate)}</span>
            </p>
          </div>

          {account && (
            <p className="text-center text-sm text-slate-500">Tu saldo: {formatCOP(account.balance)}</p>
          )}

          {(notEnoughBalance || insufficientFunds) && (
            <Alert>
              <p>No tienes saldo suficiente para pagar esta parte.</p>
              <Link to="/reload" className="mt-1 inline-block font-semibold underline">
                Recargar saldo
              </Link>
            </Alert>
          )}

          {pay.error && !insufficientFunds && (
            <Alert>
              <p>{getErrorMessage(pay.error)}</p>
            </Alert>
          )}

          <Button disabled={pay.isPending || notEnoughBalance} onClick={() => pay.mutate(charge.memberChargeId)}>
            {pay.isPending ? 'Pagando…' : `Pagar ${formatCOP(charge.amount)}`}
          </Button>
          <Button variant="secondary" disabled={pay.isPending} onClick={close}>
            Cancelar
          </Button>
        </div>
      )}
    </Sheet>
  )
}
