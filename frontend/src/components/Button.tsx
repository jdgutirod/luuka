import type { ComponentProps } from 'react'
import { buttonClasses, type ButtonVariant } from './button-styles'

type ButtonProps = ComponentProps<'button'> & {
  variant?: ButtonVariant
}

export function Button({ variant = 'primary', className = '', type = 'button', ...props }: ButtonProps) {
  return <button type={type} className={buttonClasses(variant, className)} {...props} />
}
