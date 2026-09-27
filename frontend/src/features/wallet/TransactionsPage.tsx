import { Link } from 'react-router'
import { getErrorMessage } from '../../api/errors'
import { Alert } from '../../components/Alert'
import { Button } from '../../components/Button'
import { buttonClasses } from '../../components/button-styles'
import { EmptyState } from '../../components/EmptyState'
import { ListSkeleton } from '../../components/ListSkeleton'
import { PageHeader } from '../../components/PageHeader'
import { useMyAccount } from '../accounts/api'
import { useTransactionHistory } from './api'
import { TransactionList } from './TransactionList'

export function TransactionsPage() {
  const { data: account } = useMyAccount()
  const history = useTransactionHistory()
  const transactions = history.data?.pages.flat() ?? []

  return (
    <>
      <PageHeader title="Movimientos" />

      {(history.isPending || !account) && !history.error && <ListSkeleton rows={5} />}

      {history.error && (
        <Alert onRetry={() => history.refetch()}>
          <p>{getErrorMessage(history.error)}</p>
        </Alert>
      )}

      {account && history.data && transactions.length === 0 && (
        <EmptyState
          title="Aún no tienes movimientos"
          description="Tus recargas, transferencias y pagos de cancha aparecerán aquí."
          action={
            <Link to="/reload" className={buttonClasses('primary')}>
              Recargar saldo
            </Link>
          }
        />
      )}

      {account && transactions.length > 0 && (
        <>
          <TransactionList transactions={transactions} myAccountId={account.id} groupByDay />
          {history.hasNextPage && (
            <Button
              variant="secondary"
              className="mt-4 w-full"
              disabled={history.isFetchingNextPage}
              onClick={() => history.fetchNextPage()}
            >
              {history.isFetchingNextPage ? 'Cargando…' : 'Cargar más'}
            </Button>
          )}
        </>
      )}
    </>
  )
}
