const timeFormatter = new Intl.DateTimeFormat('es-CO', { hour: 'numeric', minute: '2-digit' })
const dayFormatter = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'long' })
const dayWithYearFormatter = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'long', year: 'numeric' })
const shortDateTimeFormatter = new Intl.DateTimeFormat('es-CO', {
  day: 'numeric',
  month: 'short',
  hour: 'numeric',
  minute: '2-digit',
})

function isSameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
}

/** "3:45 p. m." */
export function formatTime(iso: string): string {
  return timeFormatter.format(new Date(iso))
}

/** "12 sept, 3:45 p. m." */
export function formatDateTime(iso: string): string {
  return shortDateTimeFormatter.format(new Date(iso))
}

/** "12 de septiembre de 2026" */
export function formatLongDate(iso: string): string {
  return dayWithYearFormatter.format(new Date(iso))
}

/** "Hoy", "Ayer", "12 de septiembre" or, for other years, "12 de septiembre de 2025". */
export function formatDay(iso: string): string {
  const date = new Date(iso)
  const today = new Date()
  const yesterday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 1)

  if (isSameDay(date, today)) {
    return 'Hoy'
  }
  if (isSameDay(date, yesterday)) {
    return 'Ayer'
  }
  return date.getFullYear() === today.getFullYear() ? dayFormatter.format(date) : dayWithYearFormatter.format(date)
}
