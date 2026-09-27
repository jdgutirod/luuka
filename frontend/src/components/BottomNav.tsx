import { useState, type ComponentType } from 'react'
import { Link, NavLink } from 'react-router'
import { useMyMemberCharges } from '../features/group-charges/api'
import { ActivityIcon, ChevronRightIcon, HomeIcon, PlusIcon, SendIcon, UserIcon, UsersIcon, WalletIcon } from './icons'
import { Sheet } from './Sheet'

type Tab = {
  to: string
  label: string
  icon: ComponentType<{ className?: string }>
  badge?: number
}

function NavItem({ to, label, icon: Icon, badge }: Tab) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) =>
        `relative flex flex-1 flex-col items-center gap-0.5 rounded-full py-1.5 text-[11px] font-medium ${
          isActive ? 'text-emerald-700' : 'text-slate-500 hover:text-slate-700'
        }`
      }
    >
      <Icon className="size-6" />
      {label}
      {badge !== undefined && badge > 0 && (
        <span className="absolute top-0 left-1/2 ml-1.5 flex min-w-4.5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
          {badge}
          <span className="sr-only"> pendientes</span>
        </span>
      )}
    </NavLink>
  )
}

const actions = [
  { to: '/reload', label: 'Recargar saldo', description: 'Agrega dinero a tu billetera', icon: WalletIcon },
  { to: '/transfer', label: 'Transferir', description: 'Envía dinero con la placa de alguien', icon: SendIcon },
  { to: '/charges/new', label: 'Dividir una cancha', description: 'Cobra a cada quien su parte', icon: UsersIcon },
]

/** Floating tab bar at the bottom, with a central button for the money actions. */
export function BottomNav() {
  const [actionsOpen, setActionsOpen] = useState(false)
  const { data: pendingCharges } = useMyMemberCharges('PENDING')

  return (
    <>
      <nav
        aria-label="Principal"
        className="fixed inset-x-0 bottom-0 z-20 px-4 pb-[max(1rem,env(safe-area-inset-bottom))]"
      >
        <div className="mx-auto flex max-w-md items-center rounded-full bg-white/95 px-2 py-1.5 shadow-lg ring-1 shadow-slate-900/10 ring-slate-200 backdrop-blur">
          <NavItem to="/" label="Inicio" icon={HomeIcon} />
          <NavItem to="/transactions" label="Movimientos" icon={ActivityIcon} />
          <div className="flex flex-1 justify-center">
            <button
              type="button"
              aria-label="Nueva operación"
              aria-haspopup="dialog"
              onClick={() => setActionsOpen(true)}
              className="-mt-8 flex size-14 items-center justify-center rounded-full bg-emerald-600 text-white shadow-lg ring-4 shadow-emerald-900/20 ring-slate-50 transition-transform hover:bg-emerald-700 active:scale-95"
            >
              <PlusIcon className="size-7" />
            </button>
          </div>
          <NavItem to="/charges" label="Cobros" icon={UsersIcon} badge={pendingCharges?.length} />
          <NavItem to="/profile" label="Perfil" icon={UserIcon} />
        </div>
      </nav>

      <Sheet open={actionsOpen} onClose={() => setActionsOpen(false)} title="¿Qué quieres hacer?">
        <ul className="flex flex-col gap-2">
          {actions.map(({ to, label, description, icon: Icon }) => (
            <li key={to}>
              <Link
                to={to}
                onClick={() => setActionsOpen(false)}
                className="flex items-center gap-3 rounded-2xl p-3 ring-1 ring-slate-200 hover:bg-slate-50"
              >
                <span className="flex size-11 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
                  <Icon />
                </span>
                <span className="flex-1">
                  <span className="block font-semibold text-slate-900">{label}</span>
                  <span className="block text-sm text-slate-500">{description}</span>
                </span>
                <ChevronRightIcon className="size-5 text-slate-400" />
              </Link>
            </li>
          ))}
        </ul>
      </Sheet>
    </>
  )
}
