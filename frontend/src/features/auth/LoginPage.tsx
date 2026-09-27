import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useLocation, useNavigate } from 'react-router'
import { z } from 'zod'
import { getErrorMessage } from '../../api/errors'
import { AuthLayout } from '../../components/AuthLayout'
import { Button } from '../../components/Button'
import { PasswordField } from '../../components/PasswordField'
import { TextField } from '../../components/TextField'
import { useAuth } from './useAuth'

const loginSchema = z.object({
  email: z.email('Escribe un email válido'),
  password: z.string().min(1, 'Escribe tu contraseña'),
})

type LoginForm = z.infer<typeof loginSchema>

export function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/'

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) })

  if (isAuthenticated) {
    return <Navigate to={from} replace />
  }

  const onSubmit = handleSubmit(async ({ email, password }) => {
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (error) {
      setError('root', { message: getErrorMessage(error) })
    }
  })

  return (
    <AuthLayout title="Inicia sesión" subtitle="Entra a tu billetera Luuka">
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        <TextField label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register('email')} />
        <PasswordField
          label="Contraseña"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register('password')}
        />
        {errors.root && (
          <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {errors.root.message}
          </p>
        )}
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Entrando…' : 'Entrar'}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500">
        ¿No tienes cuenta?{' '}
        <Link to="/register" className="font-semibold text-emerald-700 hover:underline">
          Regístrate
        </Link>
      </p>
    </AuthLayout>
  )
}
