/** Same split as the backend: equal parts in whole pesos, the leftover pesos go one by one to the first members. */
export function splitAmount(total: number, parts: number): number[] {
  const base = Math.floor(total / parts)
  const leftover = total % parts
  return Array.from({ length: parts }, (_, index) => (index < leftover ? base + 1 : base))
}

/**
 * Same as the backend's split_member_amounts: what each member is charged and the creator's own part.
 * When the creator also played, the total is split among everyone and the leftover pesos stay in the creator's part.
 */
export function splitMemberAmounts(
  total: number,
  members: number,
  creatorPlays: boolean,
): { memberAmounts: number[]; creatorShare: number } {
  if (!creatorPlays) {
    return { memberAmounts: splitAmount(total, members), creatorShare: 0 }
  }
  const part = Math.floor(total / (members + 1))
  return { memberAmounts: Array(members).fill(part), creatorShare: total - part * members }
}
