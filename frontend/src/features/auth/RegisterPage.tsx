import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useNavigate } from 'react-router'
import { z } from 'zod'
import { getErrorMessage } from '../../api/errors'
import { AuthLayout } from '../../components/AuthLayout'
import { Button } from '../../components/Button'
import { PasswordField } from '../../components/PasswordField'
import { TextField } from '../../components/TextField'
import { registerAccount } from './api'
import { useAuth } from './useAuth'

// Same limits as the backend (AccountCreate), so most mistakes are caught before sending
const registerSchema = z.object({
  owner_name: z.string().trim().min(1, 'Escribe tu nombre').max(100, 'Máximo 100 caracteres'),
  email: z.email('Escribe un email válido'),
  password: z.string().min(8, 'Mínimo 8 caracteres').max(128, 'Máximo 128 caracteres'),
})

type RegisterForm = z.infer<typeof registerSchema>

export function RegisterPage() {
  const { isAuthenticated, login } = useAuth()
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({ resolver: zodResolver(registerSchema) })

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const onSubmit = handleSubmit(async (data) => {
    try {
      await registerAccount(data)
      await login(data.email, data.password)
      navigate('/', { replace: true })
    } catch (error) {
      setError('root', { message: getErrorMessage(error) })
    }
  })

  return (
    <AuthLayout title="Crea tu cuenta" subtitle="Recibirás una placa para que otros te encuentren">
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        <TextField label="Nombre" autoComplete="name" error={errors.owner_name?.message} {...register('owner_name')} />
        <TextField label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register('email')} />
        <PasswordField
          label="Contraseña"
          autoComplete="new-password"
          error={errors.password?.message}
          {...register('password')}
        />
        {errors.root && (
          <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {errors.root.message}
          </p>
        )}
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creando cuenta…' : 'Crear cuenta'}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500">
        ¿Ya tienes cuenta?{' '}
        <Link to="/login" className="font-semibold text-emerald-700 hover:underline">
          Inicia sesión
        </Link>
      </p>
    </AuthLayout>
  )
}
