import type { ComponentProps } from 'react'
import { formatNumber } from '../lib/money'
import { TextField } from './TextField'

type AmountFieldProps = Omit<ComponentProps<typeof TextField>, 'value' | 'onChange' | 'prefix'> & {
  value: number | undefined
  onChange: (amount: number | undefined) => void
}

// Enough digits for the backend maximum ($10.000.000), without letting the number grow without end
const MAX_DIGITS = 9

/** Whole pesos, shown with thousands separators while typing: "50000" is displayed as "50.000". */
export function AmountField({ value, onChange, ...props }: AmountFieldProps) {
  return (
    <TextField
      {...props}
      prefix="$"
      inputMode="numeric"
      autoComplete="off"
      placeholder="0"
      value={value === undefined ? '' : formatNumber(value)}
      onChange={(event) => {
        const digits = event.target.value.replace(/\D/g, '').slice(0, MAX_DIGITS)
        onChange(digits === '' ? undefined : Number(digits))
      }}
    />
  )
}
