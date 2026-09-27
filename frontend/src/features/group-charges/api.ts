import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, unwrap } from '../../api/client'
import { useIdempotencyKey } from '../../api/idempotency'
import { queryKeys } from '../../api/query-keys'
import type { ChargeState, GroupChargeCreate } from '../../api/types'
import { refreshBalance } from '../wallet/api'

const CREATED_PAGE_SIZE = 20

export function useMyMemberCharges(state?: ChargeState) {
  return useQuery({
    queryKey: queryKeys.myMemberCharges(state),
    queryFn: () => unwrap(api.GET('/group-charges/member-charges/me', { params: { query: { state } } })),
  })
}

export function useCreatedGroupCharges(state?: ChargeState) {
  return useInfiniteQuery({
    queryKey: queryKeys.createdGroupCharges(state),
    queryFn: ({ pageParam }) =>
      unwrap(
        api.GET('/group-charges/created', {
          params: { query: { state, limit: CREATED_PAGE_SIZE, offset: pageParam } },
        }),
      ),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length < CREATED_PAGE_SIZE ? undefined : allPages.length * CREATED_PAGE_SIZE,
  })
}

export function useGroupCharge(id: string) {
  return useQuery({
    queryKey: queryKeys.groupCharge(id),
    queryFn: () => unwrap(api.GET('/group-charges/{group_charge_id}', { params: { path: { group_charge_id: id } } })),
  })
}

export function useCreateGroupCharge() {
  const queryClient = useQueryClient()
  const idempotencyKey = useIdempotencyKey()

  return useMutation({
    mutationFn: (data: GroupChargeCreate) =>
      unwrap(
        api.POST('/group-charges', {
          body: data,
          params: { header: { 'idempotency-key': idempotencyKey.get() } },
        }),
      ),
    onSettled: (_data, error) => idempotencyKey.settle(error),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.groupCharges }),
  })
}

/** Paying twice is safe: the backend returns the already paid charge, so it needs no Idempotency-Key. */
export function usePayMemberCharge() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (memberChargeId: string) =>
      unwrap(
        api.POST('/group-charges/member-charges/{member_charge_id}/pay', {
          params: { path: { member_charge_id: memberChargeId } },
        }),
      ),
    onSuccess: () =>
      Promise.all([
        refreshBalance(queryClient),
        queryClient.invalidateQueries({ queryKey: queryKeys.memberCharges }),
        queryClient.invalidateQueries({ queryKey: queryKeys.groupCharges }),
      ]),
  })
}
