import { useMemo, useRef } from 'react'
import { ApiError } from './errors'

function createKey(): string {
  // randomUUID only exists on https or localhost; getRandomValues works everywhere
  if (typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), (byte) => byte.toString(16).padStart(2, '0')).join('')
}

/** A network error or a 5xx does not tell whether the backend did the operation or not. */
function isUncertain(error: unknown): boolean {
  return error != null && !(error instanceof ApiError && error.status < 500)
}

/**
 * Keeps the Idempotency-Key of one operation (see the backend README):
 * - the same key while retrying an operation whose result is unknown, so it is never done twice;
 * - a new key once the operation succeeded or was rejected, because the next one is a different operation.
 */
export function useIdempotencyKey() {
  const keyRef = useRef<string | null>(null)

  return useMemo(
    () => ({
      get(): string {
        keyRef.current ??= createKey()
        return keyRef.current
      },
      /** Call it when the request ends, with its error or null if it succeeded. */
      settle(error: unknown): void {
        if (!isUncertain(error)) {
          keyRef.current = null
        }
      },
    }),
    [],
  )
}
