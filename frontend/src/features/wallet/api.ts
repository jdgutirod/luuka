import { useQuery } from '@tanstack/react-query'
import { api, unwrap } from '../../api/client'

export function useMyAccount() {
  return useQuery({
    queryKey: ['accounts', 'me'],
    queryFn: () => unwrap(api.GET('/accounts/me')),
  })
}
