import { useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { getErrorMessage } from '../../api/errors'
import type { ChargeState, GroupChargeResponse, MyMemberChargeResponse } from '../../api/types'
import { Alert } from '../../components/Alert'
import { Avatar } from '../../components/Avatar'
import { Button } from '../../components/Button'
import { buttonClasses } from '../../components/button-styles'
import { EmptyState } from '../../components/EmptyState'
import { ChevronRightIcon, PlusIcon } from '../../components/icons'
import { ListSkeleton } from '../../components/ListSkeleton'
import { PageHeader } from '../../components/PageHeader'
import { Segmented } from '../../components/Segmented'
import { StateBadge } from '../../components/StateBadge'
import { formatDay } from '../../lib/date'
import { formatCOP } from '../../lib/money'
import { useCreatedGroupCharges, useMyMemberCharges } from './api'
import { ChargeProgress } from './ChargeProgress'
import { PayChargeSheet, type ChargeToPay } from './PayChargeSheet'

type Tab = 'to-pay' | 'created'
type StateFilter = ChargeState | 'ALL'

const tabs: { value: Tab; label: string }[] = [
  { value: 'to-pay', label: 'Por pagar' },
  { value: 'created', label: 'Creados por mí' },
]

function toState(filter: StateFilter): ChargeState | undefined {
  return filter === 'ALL' ? undefined : filter
}

function MemberChargeCard({ charge, onPay }: { charge: MyMemberChargeResponse; onPay: () => void }) {
  const group = charge.group_charge
  return (
    <li className="rounded-2xl bg-white ring-1 ring-slate-200">
      <Link to={`/charges/${group.id}`} className="flex items-center gap-3 p-4">
        <Avatar name={group.creator.owner_name} />
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold text-slate-900">{group.name}</p>
          <p className="truncate text-sm text-slate-500">Te cobra {group.creator.owner_name}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <p className="font-semibold text-slate-900 tabular-nums">{formatCOP(charge.assigned_amount)}</p>
          <StateBadge state={charge.state} kind="member" />
        </div>
      </Link>
      {charge.state === 'PENDING' && (
        <div className="px-4 pb-4">
          <Button className="w-full" onClick={onPay}>
            Pagar mi parte
          </Button>
        </div>
      )}
    </li>
  )
}

function ToPayTab() {
  const [filter, setFilter] = useState<ChargeState>('PENDING')
  const [chargeToPay, setChargeToPay] = useState<ChargeToPay | null>(null)
  const { data: charges, isPending, error, refetch } = useMyMemberCharges(filter)

  return (
    <div className="flex flex-col gap-4">
      <Segmented
        variant="chips"
        label="Filtrar por estado"
        value={filter}
        onChange={setFilter}
        options={[
          { value: 'PENDING', label: 'Pendientes' },
          { value: 'COMPLETED', label: 'Pagados' },
        ]}
      />

      {isPending && <ListSkeleton />}
      {error && (
        <Alert onRetry={() => refetch()}>
          <p>{getErrorMessage(error)}</p>
        </Alert>
      )}
      {charges?.length === 0 && (
        <EmptyState
          title={filter === 'PENDING' ? 'No tienes cobros por pagar' : 'Aún no has pagado cobros'}
          description="Cuando alguien te agregue a un cobro de cancha, aparecerá aquí."
        />
      )}
      {charges && charges.length > 0 && (
        <ul className="flex flex-col gap-3">
          {charges.map((charge) => (
            <MemberChargeCard
              key={charge.id}
              charge={charge}
              onPay={() =>
                setChargeToPay({
                  memberChargeId: charge.id,
                  amount: charge.assigned_amount,
                  groupName: charge.group_charge.name,
                  creator: charge.group_charge.creator,
                })
              }
            />
          ))}
        </ul>
      )}

      <PayChargeSheet charge={chargeToPay} onClose={() => setChargeToPay(null)} />
    </div>
  )
}

function GroupChargeCard({ groupCharge }: { groupCharge: GroupChargeResponse }) {
  return (
    <li>
      <Link
        to={`/charges/${groupCharge.id}`}
        className="flex flex-col gap-3 rounded-2xl bg-white p-4 ring-1 ring-slate-200 hover:bg-slate-50"
      >
        <div className="flex items-start gap-3">
          <div className="min-w-0 flex-1">
            <p className="truncate font-semibold text-slate-900">{groupCharge.name}</p>
            <p className="text-sm text-slate-500">
              {formatCOP(groupCharge.total_amount)} · {formatDay(groupCharge.created_at)}
            </p>
          </div>
          <StateBadge state={groupCharge.state} kind="group" />
          <ChevronRightIcon className="size-5 text-slate-400" />
        </div>
        <ChargeProgress groupCharge={groupCharge} />
      </Link>
    </li>
  )
}

function CreatedTab() {
  const [filter, setFilter] = useState<StateFilter>('ALL')
  const created = useCreatedGroupCharges(toState(filter))
  const groupCharges = created.data?.pages.flat() ?? []

  return (
    <div className="flex flex-col gap-4">
      <Segmented
        variant="chips"
        label="Filtrar por estado"
        value={filter}
        onChange={setFilter}
        options={[
          { value: 'ALL', label: 'Todos' },
          { value: 'PENDING', label: 'Pendientes' },
          { value: 'COMPLETED', label: 'Completados' },
        ]}
      />

      {created.isPending && <ListSkeleton />}
      {created.error && (
        <Alert onRetry={() => created.refetch()}>
          <p>{getErrorMessage(created.error)}</p>
        </Alert>
      )}
      {created.data && groupCharges.length === 0 && (
        <EmptyState
          title="No hay cobros aquí"
          description="¿Pagaste una cancha? Crea un cobro y cada quien te paga su parte."
          action={
            <Link to="/charges/new" className={buttonClasses('primary')}>
              Dividir una cancha
            </Link>
          }
        />
      )}
      {groupCharges.length > 0 && (
        <ul className="flex flex-col gap-3">
          {groupCharges.map((groupCharge) => (
            <GroupChargeCard key={groupCharge.id} groupCharge={groupCharge} />
          ))}
        </ul>
      )}
      {created.hasNextPage && (
        <Button
          variant="secondary"
          disabled={created.isFetchingNextPage}
          onClick={() => created.fetchNextPage()}
        >
          {created.isFetchingNextPage ? 'Cargando…' : 'Cargar más'}
        </Button>
      )}
    </div>
  )
}

export function ChargesPage() {
  // The tab lives in the URL, so coming back from a charge detail keeps it
  const [searchParams, setSearchParams] = useSearchParams()
  const tab: Tab = searchParams.get('tab') === 'created' ? 'created' : 'to-pay'

  return (
    <>
      <PageHeader
        title="Cobros"
        action={
          <Link to="/charges/new" className={buttonClasses('primary', 'px-3 py-2')}>
            <PlusIcon className="size-4" />
            Nuevo
          </Link>
        }
      />

      <div className="flex flex-col gap-5">
        <Segmented
          label="Tipo de cobro"
          value={tab}
          onChange={(value) => setSearchParams(value === 'created' ? { tab: 'created' } : {}, { replace: true })}
          options={tabs}
        />
        {tab === 'to-pay' ? <ToPayTab /> : <CreatedTab />}
      </div>
    </>
  )
}
