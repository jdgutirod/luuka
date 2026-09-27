import type { GroupChargeResponse } from '../../api/types'
import { formatCOP } from '../../lib/money'

/**
 * How much of a group charge the members have paid: "2 de 3 pagaron · $40.000 de $60.000".
 * The creator's own part (when they also played) is not charged, so it is not part of what is collected.
 */
export function ChargeProgress({ groupCharge }: { groupCharge: GroupChargeResponse }) {
  const memberCharges = groupCharge.member_charges ?? []
  const toCollect = groupCharge.total_amount - groupCharge.creator_share
  const paid = memberCharges.filter((memberCharge) => memberCharge.state === 'COMPLETED')
  const collected = paid.reduce((sum, memberCharge) => sum + memberCharge.assigned_amount, 0)
  const percent = toCollect > 0 ? Math.round((collected / toCollect) * 100) : 0

  return (
    <div>
      <div
        role="progressbar"
        aria-label="Dinero recogido"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-2 overflow-hidden rounded-full bg-slate-100"
      >
        <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${percent}%` }} />
      </div>
      <p className="mt-2 flex justify-between text-xs text-slate-500">
        <span>
          {paid.length} de {memberCharges.length} pagaron
        </span>
        <span className="tabular-nums">
          {formatCOP(collected)} de {formatCOP(toCollect)}
        </span>
      </p>
    </div>
  )
}
