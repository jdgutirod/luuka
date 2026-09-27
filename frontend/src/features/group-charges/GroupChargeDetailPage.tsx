import { useState } from 'react'
import { useLocation, useParams } from 'react-router'
import { getErrorMessage } from '../../api/errors'
import { Alert } from '../../components/Alert'
import { BottomActions } from '../../components/BottomActions'
import { Button } from '../../components/Button'
import { ListSkeleton } from '../../components/ListSkeleton'
import { PageHeader } from '../../components/PageHeader'
import { StateBadge } from '../../components/StateBadge'
import { formatDateTime } from '../../lib/date'
import { formatCOP } from '../../lib/money'
import { formatPlate } from '../../lib/plate'
import { useMyAccount } from '../accounts/api'
import { PersonRow } from '../accounts/PersonRow'
import { useGroupCharge } from './api'
import { ChargeProgress } from './ChargeProgress'
import { PayChargeSheet } from './PayChargeSheet'

export function GroupChargeDetailPage() {
  const { id = '' } = useParams()
  const location = useLocation()
  const justCreated = (location.state as { created?: boolean } | null)?.created === true
  const { data: account } = useMyAccount()
  const { data: groupCharge, isPending, error, refetch } = useGroupCharge(id)
  const [payOpen, setPayOpen] = useState(false)

  const backTo = groupCharge && account && groupCharge.creator.id === account.id ? '/charges?tab=created' : '/charges'

  if (isPending || !account) {
    return (
      <>
        <PageHeader title="Cobro" backTo={backTo} />
        <ListSkeleton rows={4} />
      </>
    )
  }
  if (error) {
    return (
      <>
        <PageHeader title="Cobro" backTo={backTo} />
        <Alert onRetry={() => refetch()}>
          <p>{getErrorMessage(error)}</p>
        </Alert>
      </>
    )
  }

  const memberCharges = groupCharge.member_charges ?? []
  const isCreator = groupCharge.creator.id === account.id
  const myCharge = memberCharges.find((memberCharge) => memberCharge.account.id === account.id)

  return (
    <>
      <PageHeader title="Cobro" backTo={backTo} />

      <div className={`flex flex-col gap-5 ${myCharge?.state === 'PENDING' ? '' : 'pb-8'}`}>
        {justCreated && (
          <Alert tone="success">
            <p className="font-semibold">Cobro creado</p>
            <p>Avísale a cada persona: lo verán en «Cobros» y pagarán su parte desde su app.</p>
          </Alert>
        )}

        <section className="rounded-3xl bg-white p-5 ring-1 ring-slate-200">
          <div className="flex items-start justify-between gap-3">
            <h2 className="text-lg font-semibold text-slate-900">{groupCharge.name}</h2>
            <StateBadge state={groupCharge.state} kind="group" />
          </div>
          <p className="mt-2 text-3xl font-bold text-slate-900 tabular-nums">{formatCOP(groupCharge.total_amount)}</p>
          <p className="mt-1 text-sm text-slate-500">
            {isCreator
              ? 'Lo creaste tú'
              : `Lo creó ${groupCharge.creator.owner_name} (${formatPlate(groupCharge.creator.plate)})`}{' '}
            · {formatDateTime(groupCharge.created_at)}
          </p>
          <div className="mt-4">
            <ChargeProgress groupCharge={groupCharge} />
          </div>
        </section>

        <section>
          <h2 className="mb-2 px-1 font-semibold text-slate-900">Quiénes juegan</h2>
          <ul className="divide-y divide-slate-100 rounded-2xl bg-white px-4 ring-1 ring-slate-200">
            {groupCharge.creator_share > 0 && (
              <li className="py-3">
                <PersonRow
                  account={groupCharge.creator}
                  isMe={isCreator}
                  trailing={
                    <div className="flex flex-col items-end gap-1">
                      <span className="font-semibold text-slate-900 tabular-nums">
                        {formatCOP(groupCharge.creator_share)}
                      </span>
                      <span className="text-xs text-slate-500">Pagó la cancha</span>
                    </div>
                  }
                />
              </li>
            )}
            {memberCharges.map((memberCharge) => (
              <li key={memberCharge.id} className="py-3">
                <PersonRow
                  account={memberCharge.account}
                  isMe={memberCharge.account.id === account.id}
                  trailing={
                    <div className="flex flex-col items-end gap-1">
                      <span className="font-semibold text-slate-900 tabular-nums">
                        {formatCOP(memberCharge.assigned_amount)}
                      </span>
                      {memberCharge.state === 'COMPLETED' && memberCharge.paid_at ? (
                        <span className="text-xs text-emerald-700">Pagó el {formatDateTime(memberCharge.paid_at)}</span>
                      ) : (
                        <StateBadge state={memberCharge.state} kind="member" />
                      )}
                    </div>
                  }
                />
              </li>
            ))}
          </ul>
        </section>
      </div>

      {myCharge?.state === 'PENDING' && (
        <BottomActions>
          <Button onClick={() => setPayOpen(true)}>Pagar mi parte ({formatCOP(myCharge.assigned_amount)})</Button>
        </BottomActions>
      )}

      <PayChargeSheet
        charge={
          payOpen && myCharge
            ? {
                memberChargeId: myCharge.id,
                amount: myCharge.assigned_amount,
                groupName: groupCharge.name,
                creator: groupCharge.creator,
              }
            : null
        }
        onClose={() => setPayOpen(false)}
      />
    </>
  )
}
