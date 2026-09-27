import { useQuery, type QueryClient } from '@tanstack/react-query'
import { api, unwrap } from '../../api/client'
import { queryKeys } from '../../api/query-keys'
import type { AccountPublic } from '../../api/types'

export function useMyAccount() {
  return useQuery({
    queryKey: queryKeys.myAccount,
    queryFn: () => unwrap(api.GET('/accounts/me')),
  })
}

/** Finds who owns a plate. Cached for a minute, so looking up the same person twice is instant. */
export function lookupAccount(queryClient: QueryClient, plate: string): Promise<AccountPublic> {
  return queryClient.fetchQuery({
    queryKey: queryKeys.accountLookup(plate),
    queryFn: () => unwrap(api.GET('/accounts/lookup', { params: { query: { plate } } })),
    staleTime: 60_000,
  })
}
