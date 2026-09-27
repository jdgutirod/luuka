import type { TransactionResponse } from '../../api/types'
import { ArrowDownLeftIcon, ArrowUpRightIcon } from '../../components/icons'
import { formatDateTime, formatDay, formatTime } from '../../lib/date'
import { formatCOP } from '../../lib/money'
import { formatPlate } from '../../lib/plate'

type TransactionListProps = {
  transactions: TransactionResponse[]
  myAccountId: string
  /** Splits the list under "Hoy", "Ayer"… headings; otherwise each row shows its full date */
  groupByDay?: boolean
}

/** What a movement means for the current account: money in or out, and with whom. */
function describe(transaction: TransactionResponse, myAccountId: string) {
  const incoming = transaction.to_account?.id === myAccountId
  const counterpart = incoming ? transaction.from_account : transaction.to_account
  const person = counterpart ? `${counterpart.owner_name} · ${formatPlate(counterpart.plate)}` : ''

  switch (transaction.type) {
    case 'RELOAD':
      return { incoming: true, title: 'Recarga', detail: 'A tu billetera' }
    case 'DIRECT_TRANSFER':
      return { incoming, title: incoming ? 'Transferencia recibida' : 'Transferencia enviada', detail: person }
    case 'COURT_PAYMENT':
      return { incoming, title: incoming ? 'Te pagaron una cancha' : 'Pagaste una cancha', detail: person }
  }
}

function TransactionItem({ transaction, myAccountId, showDate }: { transaction: TransactionResponse; myAccountId: string; showDate: boolean }) {
  const { incoming, title, detail } = describe(transaction, myAccountId)
  const when = showDate ? formatDateTime(transaction.created_at) : formatTime(transaction.created_at)

  return (
    <li className="flex items-center gap-3 py-3">
      <span
        className={`flex size-10 shrink-0 items-center justify-center rounded-full ${
          incoming ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
        }`}
      >
        {incoming ? <ArrowDownLeftIcon /> : <ArrowUpRightIcon />}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium text-slate-900">{title}</p>
        <p className="truncate text-sm text-slate-500">{detail}</p>
      </div>
      <div className="text-right">
        <p className={`font-semibold tabular-nums ${incoming ? 'text-emerald-700' : 'text-slate-900'}`}>
          <span className="sr-only">{incoming ? 'Entrada de' : 'Salida de'} </span>
          <span aria-hidden="true">{incoming ? '+' : '−'}</span>
          {formatCOP(transaction.amount)}
        </p>
        <p className="text-xs text-slate-400">{when}</p>
      </div>
    </li>
  )
}

function groupByDayLabel(transactions: TransactionResponse[]): [string, TransactionResponse[]][] {
  const groups = new Map<string, TransactionResponse[]>()
  for (const transaction of transactions) {
    const day = formatDay(transaction.created_at)
    groups.set(day, [...(groups.get(day) ?? []), transaction])
  }
  return [...groups]
}

export function TransactionList({ transactions, myAccountId, groupByDay = false }: TransactionListProps) {
  if (!groupByDay) {
    return (
      <ul className="divide-y divide-slate-100 rounded-2xl bg-white px-4 ring-1 ring-slate-200">
        {transactions.map((transaction) => (
          <TransactionItem key={transaction.id} transaction={transaction} myAccountId={myAccountId} showDate />
        ))}
      </ul>
    )
  }

  return (
    <div className="flex flex-col gap-5">
      {groupByDayLabel(transactions).map(([day, dayTransactions]) => (
        <section key={day}>
          <h2 className="mb-2 px-1 text-sm font-semibold text-slate-500">{day}</h2>
          <ul className="divide-y divide-slate-100 rounded-2xl bg-white px-4 ring-1 ring-slate-200">
            {dayTransactions.map((transaction) => (
              <TransactionItem
                key={transaction.id}
                transaction={transaction}
                myAccountId={myAccountId}
                showDate={false}
              />
            ))}
          </ul>
        </section>
      ))}
    </div>
  )
}
