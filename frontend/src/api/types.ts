import type { components } from './schema'

type Schemas = components['schemas']

export type AccountCreate = Schemas['AccountCreate']
export type AccountResponse = Schemas['AccountResponse']
export type AccountPublic = Schemas['AccountPublic']

export type TransactionType = Schemas['TransactionType']
export type TransactionResponse = Schemas['TransactionResponse']

export type ChargeState = Schemas['ChargeState']
export type GroupChargeCreate = Schemas['GroupChargeCreate']
export type GroupChargeResponse = Schemas['GroupChargeResponse']
export type MemberChargeResponse = Schemas['MemberChargeResponse']
export type MyMemberChargeResponse = Schemas['MyMemberChargeResponse']
