import { z } from 'zod'

const copFormatter = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  maximumFractionDigits: 0,
})

const numberFormatter = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 })

/** Formats whole pesos for display, e.g. 90000 → "$ 90.000". */
export function formatCOP(amount: number): string {
  return copFormatter.format(amount)
}

/** Formats a number with thousands separators and no currency sign, e.g. 90000 → "90.000". */
export function formatNumber(amount: number): string {
  return numberFormatter.format(amount)
}

// Default limits of the backend (MIN_TRANSACTION_AMOUNT and MAX_TRANSACTION_AMOUNT). The backend is the one
// that enforces them; here they only give an early message in the forms.
export const MIN_AMOUNT = 1_000
export const MAX_AMOUNT = 10_000_000

export const amountSchema = z
  .number({ error: 'Escribe un monto' })
  .int('El monto debe ser en pesos enteros')
  .min(MIN_AMOUNT, `El monto mínimo es ${formatCOP(MIN_AMOUNT)}`)
  .max(MAX_AMOUNT, `El monto máximo es ${formatCOP(MAX_AMOUNT)}`)
