import type { ReactNode } from 'react'
import { BottomActions } from './BottomActions'
import { CheckIcon } from './icons'

type SuccessScreenProps = {
  title: string
  amount?: string
  description?: ReactNode
  /** Buttons or links to continue, shown at the bottom of the screen */
  children: ReactNode
}

/** Confirmation shown after an operation that moved money. */
export function SuccessScreen({ title, amount, description, children }: SuccessScreenProps) {
  return (
    <>
      <section role="status" className="flex flex-col items-center pt-16 text-center">
        <span className="flex size-20 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
          <CheckIcon className="size-10" />
        </span>
        <h1 className="mt-6 text-xl font-semibold text-slate-900">{title}</h1>
        {amount && <p className="mt-2 text-4xl font-bold text-slate-900 tabular-nums">{amount}</p>}
        {description && <p className="mt-3 text-slate-500">{description}</p>}
      </section>
      <BottomActions>{children}</BottomActions>
    </>
  )
}
