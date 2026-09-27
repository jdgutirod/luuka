type SegmentedProps<T extends string> = {
  label: string
  options: { value: T; label: string }[]
  value: T
  onChange: (value: T) => void
  /** "tabs" fills the width, like an iOS segmented control; "chips" are small pills for filters */
  variant?: 'tabs' | 'chips'
}

export function Segmented<T extends string>({ label, options, value, onChange, variant = 'tabs' }: SegmentedProps<T>) {
  if (variant === 'chips') {
    return (
      <div role="group" aria-label={label} className="flex gap-2 overflow-x-auto">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            aria-pressed={option.value === value}
            onClick={() => onChange(option.value)}
            className="shrink-0 rounded-full border border-slate-300 bg-white px-3.5 py-1.5 text-sm font-medium text-slate-600 aria-pressed:border-emerald-600 aria-pressed:bg-emerald-600 aria-pressed:text-white"
          >
            {option.label}
          </button>
        ))}
      </div>
    )
  }

  return (
    <div role="group" aria-label={label} className="flex rounded-xl bg-slate-200/70 p-1">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={option.value === value}
          onClick={() => onChange(option.value)}
          className="flex-1 rounded-lg py-2 text-sm font-semibold text-slate-600 aria-pressed:bg-white aria-pressed:text-slate-900 aria-pressed:shadow-sm"
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
