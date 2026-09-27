import { zodResolver } from '@hookform/resolvers/zod'
import { useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { getErrorMessage } from '../../api/errors'
import type { AccountPublic } from '../../api/types'
import { Button } from '../../components/Button'
import { TextField } from '../../components/TextField'
import { isValidPlate, normalizePlate } from '../../lib/plate'
import { lookupAccount } from './api'

const plateSchema = z.object({
  plate: z
    .string()
    .refine((plate) => isValidPlate(normalizePlate(plate)), 'La placa tiene 3 letras y 3 números, por ejemplo KQX-482'),
})

type PlateForm = z.infer<typeof plateSchema>

type PlateSearchProps = {
  label: string
  hint?: string
  /** Returns why this account cannot be chosen (e.g. it is your own), or null when it can */
  validate?: (account: AccountPublic) => string | null
  onFound: (account: AccountPublic) => void
}

/** Finds a person by their plate. The screen then shows the name so the user confirms it is the right person. */
export function PlateSearch({ label, hint, validate, onFound }: PlateSearchProps) {
  const queryClient = useQueryClient()
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<PlateForm>({ resolver: zodResolver(plateSchema), defaultValues: { plate: '' } })

  const onSubmit = handleSubmit(async ({ plate }) => {
    try {
      const account = await lookupAccount(queryClient, normalizePlate(plate))
      const problem = validate?.(account)
      if (problem) {
        setError('plate', { message: problem })
        return
      }
      reset()
      onFound(account)
    } catch (error) {
      setError('plate', { message: getErrorMessage(error) })
    }
  })

  return (
    <form onSubmit={onSubmit} noValidate>
      <TextField
        label={label}
        hint={hint}
        placeholder="KQX-482"
        autoCapitalize="characters"
        autoComplete="off"
        autoCorrect="off"
        spellCheck={false}
        maxLength={8}
        className="font-mono uppercase placeholder:normal-case"
        error={errors.plate?.message}
        action={
          <Button type="submit" variant="secondary" disabled={isSubmitting}>
            {isSubmitting ? 'Buscando…' : 'Buscar'}
          </Button>
        }
        {...register('plate')}
      />
    </form>
  )
}
