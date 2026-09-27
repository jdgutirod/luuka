import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { Link } from 'react-router'
import { z } from 'zod'
import { getErrorMessage } from '../../api/errors'
import type { AccountPublic } from '../../api/types'
import { Alert } from '../../components/Alert'
import { AmountField } from '../../components/AmountField'
import { BottomActions } from '../../components/BottomActions'
import { Button } from '../../components/Button'
import { buttonClasses } from '../../components/button-styles'
import { PageHeader } from '../../components/PageHeader'
import { SuccessScreen } from '../../components/SuccessScreen'
import { amountSchema, formatCOP } from '../../lib/money'
import { formatPlate } from '../../lib/plate'
import { useMyAccount } from '../accounts/api'
import { PersonRow } from '../accounts/PersonRow'
import { PlateSearch } from '../accounts/PlateSearch'
import { useTransfer } from './api'

const amountFormSchema = z.object({ amount: amountSchema })

type AmountForm = z.infer<typeof amountFormSchema>

function RecipientCard({ recipient, onChange }: { recipient: AccountPublic; onChange: () => void }) {
  return (
    <section className="rounded-2xl bg-white p-4 ring-1 ring-slate-200">
      <p className="mb-3 text-sm font-medium text-slate-500">Para</p>
      <PersonRow
        account={recipient}
        trailing={
          <Button variant="ghost" className="px-3 py-2" onClick={onChange}>
            Cambiar
          </Button>
        }
      />
    </section>
  )
}

type AmountStepProps = {
  balance: number | undefined
  defaultAmount: number | undefined
  onContinue: (amount: number) => void
}

function AmountStep({ balance, defaultAmount, onContinue }: AmountStepProps) {
  const {
    control,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<AmountForm>({ resolver: zodResolver(amountFormSchema), defaultValues: { amount: defaultAmount } })

  const onSubmit = handleSubmit(({ amount }) => {
    // The backend checks it again; this only avoids a round trip that is sure to fail
    if (balance !== undefined && amount > balance) {
      setError('amount', { message: `No tienes saldo suficiente. Disponible: ${formatCOP(balance)}` })
      return
    }
    onContinue(amount)
  })

  return (
    <form onSubmit={onSubmit} noValidate className="mt-5 flex flex-1 flex-col">
      <Controller
        control={control}
        name="amount"
        render={({ field }) => (
          <AmountField
            label="¿Cuánto quieres enviar?"
            error={errors.amount?.message}
            hint={balance !== undefined && <>Disponible: {formatCOP(balance)}</>}
            autoFocus
            {...field}
          />
        )}
      />
      <BottomActions>
        <Button type="submit">Continuar</Button>
      </BottomActions>
    </form>
  )
}

export function TransferPage() {
  const { data: account } = useMyAccount()
  const transfer = useTransfer()
  const [recipient, setRecipient] = useState<AccountPublic | null>(null)
  const [amount, setAmount] = useState<number | undefined>(undefined)
  const [confirming, setConfirming] = useState(false)

  const startOver = () => {
    setRecipient(null)
    setAmount(undefined)
    setConfirming(false)
    transfer.reset()
  }

  if (transfer.isSuccess && recipient) {
    return (
      <SuccessScreen
        title="Transferencia enviada"
        amount={formatCOP(transfer.data.amount)}
        description={
          <>
            {recipient.owner_name} ({formatPlate(recipient.plate)}) ya tiene el dinero en su billetera.
          </>
        }
      >
        <Link to="/" className={buttonClasses('primary')}>
          Volver al inicio
        </Link>
        <Button variant="secondary" onClick={startOver}>
          Hacer otra transferencia
        </Button>
      </SuccessScreen>
    )
  }

  return (
    <>
      <PageHeader title="Transferir" backTo="/" />

      {!recipient && (
        <PlateSearch
          label="Placa de quien recibe"
          hint="Pídele a la persona su placa. La encuentra en su perfil."
          validate={(found) => (found.id === account?.id ? 'Esa es tu propia placa' : null)}
          onFound={setRecipient}
        />
      )}

      {recipient && !confirming && (
        <>
          <RecipientCard recipient={recipient} onChange={startOver} />
          <AmountStep
            balance={account?.balance}
            defaultAmount={amount}
            onContinue={(value) => {
              setAmount(value)
              setConfirming(true)
            }}
          />
        </>
      )}

      {recipient && confirming && amount !== undefined && (
        <>
          <div className="flex flex-col gap-5">
            <section className="rounded-3xl bg-white p-6 text-center ring-1 ring-slate-200">
              <p className="text-sm text-slate-500">Vas a enviar</p>
              <p className="mt-1 text-4xl font-bold text-slate-900 tabular-nums">{formatCOP(amount)}</p>
              <p className="mt-4 text-sm text-slate-500">a</p>
              <p className="font-semibold text-slate-900">{recipient.owner_name}</p>
              <p className="font-mono text-sm text-slate-500">{formatPlate(recipient.plate)}</p>
            </section>

            {transfer.error && (
              <Alert>
                <p>{getErrorMessage(transfer.error)}</p>
              </Alert>
            )}
          </div>

          <BottomActions>
            <Button
              disabled={transfer.isPending}
              onClick={() => transfer.mutate({ toAccountId: recipient.id, amount })}
            >
              {transfer.isPending ? 'Enviando…' : `Enviar ${formatCOP(amount)}`}
            </Button>
            <Button
              variant="secondary"
              disabled={transfer.isPending}
              onClick={() => {
                setConfirming(false)
                transfer.reset()
              }}
            >
              Cambiar el monto
            </Button>
          </BottomActions>
        </>
      )}
    </>
  )
}
