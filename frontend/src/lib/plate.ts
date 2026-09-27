const PLATE_PATTERN = /^[A-Z]{3}\d{3}$/

/** Formats a plate for display like a car plate, e.g. "KQX482" → "KQX-482". */
export function formatPlate(plate: string): string {
  return `${plate.slice(0, 3)}-${plate.slice(3)}`
}

/** Same normalization as the backend: accepts the plate as people write it, "kqx-482", "KQX 482" or "KQX482". */
export function normalizePlate(plate: string): string {
  return plate.replace(/[-\s]/g, '').toUpperCase()
}

/** A normalized plate has 3 letters and 3 digits. */
export function isValidPlate(plate: string): boolean {
  return PLATE_PATTERN.test(plate)
}
