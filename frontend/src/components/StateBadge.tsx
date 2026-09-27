import type { ChargeState } from '../api/types'

type StateBadgeProps = {
  state: ChargeState
  /** A member charge is "Pagado"; a group charge is "Completado" when everyone paid */
  kind: 'member' | 'group'
}

const labels = {
  member: { PENDING: 'Pendiente', COMPLETED: 'Pagado' },
  group: { PENDING: 'Pendiente', COMPLETED: 'Completado' },
}

const styles = {
  PENDING: 'bg-amber-100 text-amber-800',
  COMPLETED: 'bg-emerald-100 text-emerald-800',
}

export function StateBadge({ state, kind }: StateBadgeProps) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${styles[state]}`}>
      {labels[kind][state]}
    </span>
  )
}
