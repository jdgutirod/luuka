/** Formats a plate for display like a car plate, e.g. "KQX482" → "KQX-482". */
export function formatPlate(plate: string): string {
  return `${plate.slice(0, 3)}-${plate.slice(3)}`
}
