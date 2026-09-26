const copFormatter = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  maximumFractionDigits: 0,
})

/** Formats whole pesos for display, e.g. 90000 → "$ 90.000". */
export function formatCOP(amount: number): string {
  return copFormatter.format(amount)
}
