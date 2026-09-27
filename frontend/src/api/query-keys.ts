import type { ChargeState } from './types'

// All the cache keys in one place, so a mutation in one feature can refresh the data of another
export const queryKeys = {
  myAccount: ['accounts', 'me'],
  accountLookup: (plate: string) => ['accounts', 'lookup', plate],

  transactions: ['transactions'],
  recentTransactions: (limit: number) => ['transactions', 'recent', limit],
  transactionHistory: ['transactions', 'history'],

  groupCharges: ['group-charges'],
  createdGroupCharges: (state: ChargeState | undefined) => ['group-charges', 'created', state ?? 'ALL'],
  groupCharge: (id: string) => ['group-charges', 'detail', id],

  memberCharges: ['member-charges'],
  myMemberCharges: (state: ChargeState | undefined) => ['member-charges', state ?? 'ALL'],
} as const
