import type { ReactNode } from 'react'
import { Button } from './Button'

type AlertProps = {
  children: ReactNode
  tone?: 'error' | 'success'
  onRetry?: () => void
}

const tones = {
  error: 'bg-red-50 text-red-700',
  success: 'bg-emerald-50 text-emerald-800',
}

export function Alert({ children, tone = 'error', onRetry }: AlertProps) {
  return (
    <div role={tone === 'error' ? 'alert' : 'status'} className={`rounded-xl px-4 py-3 text-sm ${tones[tone]}`}>
      {children}
      {onRetry && (
        <Button variant="secondary" className="mt-3 w-full" onClick={onRetry}>
          Reintentar
        </Button>
      )}
    </div>
  )
}
