import { useInfiniteQuery, useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { api, unwrap } from '../../api/client'
import { useIdempotencyKey } from '../../api/idempotency'
import { queryKeys } from '../../api/query-keys'

const HISTORY_PAGE_SIZE = 20

/** After money moves, the balance and the history shown are outdated. */
export function refreshBalance(queryClient: QueryClient): Promise<void> {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: queryKeys.myAccount }),
    queryClient.invalidateQueries({ queryKey: queryKeys.transactions }),
  ]).then(() => undefined)
}

export function useRecentTransactions(limit: number) {
  return useQuery({
    queryKey: queryKeys.recentTransactions(limit),
    queryFn: () => unwrap(api.GET('/accounts/me/transactions', { params: { query: { limit } } })),
  })
}

export function useTransactionHistory() {
  return useInfiniteQuery({
    queryKey: queryKeys.transactionHistory,
    queryFn: ({ pageParam }) =>
      unwrap(
        api.GET('/accounts/me/transactions', { params: { query: { limit: HISTORY_PAGE_SIZE, offset: pageParam } } }),
      ),
    initialPageParam: 0,
    // A page shorter than the page size is the last one
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length < HISTORY_PAGE_SIZE ? undefined : allPages.length * HISTORY_PAGE_SIZE,
  })
}

export function useReload() {
  const queryClient = useQueryClient()
  const idempotencyKey = useIdempotencyKey()

  return useMutation({
    mutationFn: (amount: number) =>
      unwrap(
        api.POST('/transactions/reloads', {
          body: { amount },
          params: { header: { 'idempotency-key': idempotencyKey.get() } },
        }),
      ),
    onSettled: (_data, error) => idempotencyKey.settle(error),
    onSuccess: () => refreshBalance(queryClient),
  })
}

export function useTransfer() {
  const queryClient = useQueryClient()
  const idempotencyKey = useIdempotencyKey()

  return useMutation({
    mutationFn: ({ toAccountId, amount }: { toAccountId: string; amount: number }) =>
      unwrap(
        api.POST('/transactions/transfers', {
          body: { to_account_id: toAccountId, amount },
          params: { header: { 'idempotency-key': idempotencyKey.get() } },
        }),
      ),
    onSettled: (_data, error) => idempotencyKey.settle(error),
    onSuccess: () => refreshBalance(queryClient),
  })
}
