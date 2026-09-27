import type { ReactNode } from 'react'

/**
 * Main buttons of a step-by-step screen, always at the bottom of the screen: pushed down when the content is short,
 * and stuck to the bottom while scrolling when it is long. Must be the last child of the page (see AppLayout)
 * or of a form that fills the rest of it (`flex flex-1 flex-col`).
 */
export function BottomActions({ children }: { children: ReactNode }) {
  return (
    <div className="sticky bottom-0 z-10 -mx-4 mt-auto flex flex-col gap-3 bg-slate-50/95 px-4 pt-6 pb-[max(1.5rem,env(safe-area-inset-bottom))] backdrop-blur">
      {children}
    </div>
  )
}
