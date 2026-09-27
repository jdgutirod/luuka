/** Placeholder rows while a list loads. */
export function ListSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div aria-busy="true" aria-label="Cargando" className="flex flex-col gap-3">
      {Array.from({ length: rows }, (_, index) => (
        <div key={index} className="flex animate-pulse items-center gap-3 rounded-2xl bg-white p-4 ring-1 ring-slate-200">
          <div className="size-11 rounded-full bg-slate-200" />
          <div className="flex flex-1 flex-col gap-2">
            <div className="h-3.5 w-1/2 rounded bg-slate-200" />
            <div className="h-3 w-1/3 rounded bg-slate-100" />
          </div>
        </div>
      ))}
    </div>
  )
}
