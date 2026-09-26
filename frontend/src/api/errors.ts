export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * Turns any error into a message for the user. The backend answers with two shapes:
 * business errors as { detail: "message" } and validation errors (422) as { detail: [{ msg, ... }] }.
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message
  }
  if (error instanceof TypeError) {
    return 'No se pudo conectar con el servidor. Revisa tu conexión e intenta de nuevo.'
  }
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    const { detail } = error
    if (typeof detail === 'string') {
      return detail
    }
    if (Array.isArray(detail)) {
      return 'Los datos enviados no son válidos. Revísalos e intenta de nuevo.'
    }
  }
  return 'Ocurrió un error inesperado. Intenta de nuevo.'
}
