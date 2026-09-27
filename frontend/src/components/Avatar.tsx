type AvatarProps = {
  name: string
  size?: 'sm' | 'md' | 'lg'
}

const sizes = {
  sm: 'size-9 text-xs',
  md: 'size-11 text-sm',
  lg: 'size-16 text-xl',
}

function initials(name: string): string {
  const words = name.trim().split(/\s+/)
  const letters = words.length > 1 ? words[0][0] + words[words.length - 1][0] : words[0].slice(0, 2)
  return letters.toUpperCase()
}

export function Avatar({ name, size = 'md' }: AvatarProps) {
  return (
    <span
      aria-hidden="true"
      className={`inline-flex shrink-0 items-center justify-center rounded-full bg-emerald-100 font-semibold text-emerald-800 ${sizes[size]}`}
    >
      {initials(name)}
    </span>
  )
}
