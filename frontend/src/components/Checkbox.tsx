import { useId, type ComponentProps } from 'react'

type CheckboxProps = Omit<ComponentProps<'input'>, 'type'> & {
  label: string
  description?: string
}

/** A checkbox with its label and an explanation, as a whole tappable card. */
export function Checkbox({ label, description, ...inputProps }: CheckboxProps) {
  const id = useId()
  const descriptionId = `${id}-description`

  return (
    <label
      htmlFor={id}
      className="flex cursor-pointer items-start gap-3 rounded-2xl bg-white p-4 ring-1 ring-slate-200 has-checked:bg-emerald-50 has-checked:ring-emerald-300"
    >
      <input
        id={id}
        type="checkbox"
        aria-describedby={description ? descriptionId : undefined}
        className="mt-0.5 size-5 shrink-0 accent-emerald-600"
        {...inputProps}
      />
      <span>
        <span className="block font-semibold text-slate-900">{label}</span>
        {description && (
          <span id={descriptionId} className="block text-sm text-slate-500">
            {description}
          </span>
        )}
      </span>
    </label>
  )
}
