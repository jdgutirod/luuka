import { useId, type ComponentProps, type ReactNode } from 'react'

type TextFieldProps = ComponentProps<'input'> & {
  label: string
  error?: string
  hint?: ReactNode
  /** Shown inside the box before the value, e.g. "$" */
  prefix?: string
  /** Shown inside the box after the value, e.g. the button that shows the password */
  suffix?: ReactNode
  /** Shown next to the box, e.g. a "Buscar" button */
  action?: ReactNode
}

export function TextField({ label, error, hint, prefix, suffix, action, className = '', ...inputProps }: TextFieldProps) {
  const id = useId()
  const errorId = `${id}-error`
  const hintId = `${id}-hint`
  const describedBy = [error && errorId, hint && hintId].filter(Boolean).join(' ') || undefined

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-slate-700">
        {label}
      </label>
      <div className="flex gap-2">
        <div
          className={`flex min-w-0 flex-1 items-center rounded-xl border bg-white focus-within:ring-2 ${
            error
              ? 'border-red-500 focus-within:ring-red-100'
              : 'border-slate-300 focus-within:border-emerald-600 focus-within:ring-emerald-100'
          }`}
        >
          {prefix && <span className="pl-3 text-slate-500">{prefix}</span>}
          <input
            id={id}
            aria-invalid={error ? true : undefined}
            aria-describedby={describedBy}
            className={`w-full min-w-0 rounded-xl bg-transparent px-3 py-3 text-slate-900 outline-none placeholder:text-slate-400 ${className}`}
            {...inputProps}
          />
          {suffix}
        </div>
        {action}
      </div>
      {hint && !error && (
        <p id={hintId} className="text-sm text-slate-500">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} className="text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  )
}
