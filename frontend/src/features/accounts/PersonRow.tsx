import type { ReactNode } from 'react'
import type { AccountPublic } from '../../api/types'
import { Avatar } from '../../components/Avatar'
import { formatPlate } from '../../lib/plate'

type PersonRowProps = {
  account: AccountPublic
  /** Marks the current user, e.g. "(tú)" */
  isMe?: boolean
  /** Shown on the right, e.g. an amount or a "Quitar" button */
  trailing?: ReactNode
}

/** Another person as the app shows them: name and plate, never their email or balance. */
export function PersonRow({ account, isMe = false, trailing }: PersonRowProps) {
  return (
    <div className="flex items-center gap-3">
      <Avatar name={account.owner_name} />
      <div className="min-w-0 flex-1">
        <p className="truncate font-semibold text-slate-900">
          {account.owner_name}
          {isMe && <span className="font-normal text-slate-500"> (tú)</span>}
        </p>
        <p className="font-mono text-sm text-slate-500">{formatPlate(account.plate)}</p>
      </div>
      {trailing}
    </div>
  )
}
