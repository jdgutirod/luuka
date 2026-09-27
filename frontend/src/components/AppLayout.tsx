import { Outlet } from 'react-router'
import { BottomNav } from './BottomNav'

type AppLayoutProps = {
  /** Main tabs show the floating nav; step-by-step screens (transfer, reload…) hide it and use a back arrow */
  withNav?: boolean
}

/**
 * Layout of the screens with a session: a phone-width column, centered on bigger screens.
 * The column fills the screen height, so a page's BottomActions can sit at the bottom.
 */
export function AppLayout({ withNav = false }: AppLayoutProps) {
  return (
    <div className="min-h-dvh">
      <main className={`mx-auto flex min-h-dvh max-w-md flex-col px-4 pt-6 ${withNav ? 'pb-32' : ''}`}>
        <Outlet />
      </main>
      {withNav && <BottomNav />}
    </div>
  )
}
