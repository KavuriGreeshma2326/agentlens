import type { ReactNode } from 'react'

interface TopBannerProps {
  tone: 'info' | 'warning'
  children: ReactNode
}

/** A message bar pinned to the top of the screen. */
export default function TopBanner({ tone, children }: TopBannerProps) {
  const colours =
    tone === 'warning'
      ? 'bg-amber-500/90 text-gray-950'
      : 'bg-indigo-500/90 text-white'

  return (
    <div
      role="status"
      className={`fixed inset-x-0 top-0 z-50 px-4 py-2 text-center text-sm font-medium ${colours}`}
    >
      {children}
    </div>
  )
}