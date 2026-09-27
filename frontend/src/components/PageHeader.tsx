import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { ArrowLeftIcon } from './icons'

type PageHeaderProps = {
  title: string
  /** Where the back arrow goes; without it there is no back arrow (main tabs) */
  backTo?: string
  action?: ReactNode
}

export function PageHeader({ title, backTo, action }: PageHeaderProps) {
  return (
    <header className="mb-6 flex items-center gap-2">
      {backTo && (
        <Link
          to={backTo}
          aria-label="Volver"
          className="-ml-2 rounded-full p-2 text-slate-700 hover:bg-slate-200/60"
        >
          <ArrowLeftIcon />
        </Link>
      )}
      <h1 className="flex-1 text-2xl font-semibold text-slate-900">{title}</h1>
      {action}
    </header>
  )
}
