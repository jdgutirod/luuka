import { zodResolver } from '@hookform/resolvers/zod'
import { Controller, useForm } from 'react-hook-form'
import { Link } from 'react-router'
import { z } from 'zod'
import { getErrorMessage } from '../../api/errors'
import { Alert } from '../../components/Alert'
import { AmountField } from '../../components/AmountField'
import { BottomActions } from '../../components/BottomActions'
import { Button } from '../../components/Button'
import { buttonClasses } from '../../components/button-styles'
import { PageHeader } from '../../components/PageHeader'
import { SuccessScreen } from '../../components/SuccessScreen'
import { amountSchema, formatCOP } from '../../lib/money'
import { useMyAccount } from '../accounts/api'
import { useReload } from './api'

const QUICK_AMOUNTS = [20_000, 50_000, 100_000, 200_000]

const reloadSchema = z.object({ amount: amountSchema })

type ReloadForm = z.infer<typeof reloadSchema>

export function ReloadPage() {
  const reload = useReload()
  const { data: account } = useMyAccount()
  const {
    control,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm<ReloadForm>({ resolver: zodResolver(reloadSchema) })

  if (reload.isSuccess) {
    return (
      <SuccessScreen
        title="Recarga exitosa"
        amount={formatCOP(reload.data.amount)}
        description={account && <>Tu saldo ahora es {formatCOP(account.balance)}</>}
      >
        <Link to="/" className={buttonClasses('primary')}>
          Volver al inicio
        </Link>
        <Button
          variant="secondary"
          onClick={() => {
            reset()
            reload.reset()
          }}
        >
          Hacer otra recarga
        </Button>
      </SuccessScreen>
    )
  }

  const onSubmit = handleSubmit(({ amount }) => reload.mutate(amount))

  return (
    <>
      <PageHeader title="Recargar saldo" backTo="/" />

      <form onSubmit={onSubmit} noValidate className="flex flex-1 flex-col gap-5">
        <Controller
          control={control}
          name="amount"
          render={({ field }) => (
            <AmountField
              label="¿Cuánto quieres recargar?"
              error={errors.amount?.message}
              hint={account && <>Saldo actual: {formatCOP(account.balance)}</>}
              autoFocus
              {...field}
            />
          )}
        />

        <div role="group" aria-label="Montos sugeridos" className="grid grid-cols-4 gap-2">
          {QUICK_AMOUNTS.map((amount) => (
            <button
              key={amount}
              type="button"
              aria-label={formatCOP(amount)}
              onClick={() => setValue('amount', amount, { shouldValidate: true })}
              className="rounded-xl bg-white py-2 text-sm font-semibold text-slate-700 ring-1 ring-slate-200 hover:bg-emerald-50 hover:text-emerald-800"
            >
              ${amount / 1000}k
            </button>
          ))}
        </div>

        {reload.error && (
          <Alert>
            <p>{getErrorMessage(reload.error)}</p>
          </Alert>
        )}

        <BottomActions>
          <Button type="submit" disabled={reload.isPending}>
            {reload.isPending ? 'Recargando…' : 'Recargar'}
          </Button>
        </BottomActions>
      </form>
    </>
  )
}
