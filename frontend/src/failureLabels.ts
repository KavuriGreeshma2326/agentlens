export interface FailureLabelInfo {
  title: string
  description: string
  badge: string
}

const UNKNOWN_BADGE = 'bg-gray-400/10 text-gray-400'

export const FAILURE_LABELS: Record<string, FailureLabelInfo> = {
  loop: {
    title: 'Loop',
    description: 'Repeated the same tool call without making progress',
    badge: 'bg-orange-400/10 text-orange-400',
  },
  wrong_tool: {
    title: 'Wrong tool',
    description: 'Called a tool that cannot do the job',
    badge: 'bg-red-400/10 text-red-400',
  },
  gave_up: {
    title: 'Gave up',
    description: 'Ended by saying it could not finish',
    badge: 'bg-yellow-400/10 text-yellow-400',
  },
  bad_output: {
    title: 'Bad output',
    description: 'Finished, but the answer was wrong',
    badge: 'bg-pink-400/10 text-pink-400',
  },
  incomplete: {
    title: 'Incomplete',
    description: 'Ended without a final answer',
    badge: UNKNOWN_BADGE,
  },
  unknown: {
    title: 'Unknown',
    description: 'No rule matched this failure',
    badge: UNKNOWN_BADGE,
  },
}

/** The causes that always appear on the dashboard, in this order. */
export const MAIN_FAILURE_LABELS: string[] = [
  'loop',
  'wrong_tool',
  'gave_up',
  'bad_output',
]

export function labelInfo(label: string): FailureLabelInfo {
  return (
    FAILURE_LABELS[label] ?? {
      title: label,
      description: '',
      badge: UNKNOWN_BADGE,
    }
  )
}