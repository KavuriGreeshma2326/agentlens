export function formatCost(cost: number): string {
  return `$${cost.toFixed(5)}`
}

export function formatLatency(ms: number): string {
  return `${(ms / 1000).toFixed(2)} s`
}

export function formatTime(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString() : '-'
}