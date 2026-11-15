import { useEffect, useState } from 'react'
import { subscribeSlow } from './api'

/** True while any request to the API is taking unusually long. */
export function useServerWaking(): boolean {
  const [waking, setWaking] = useState(false)

  useEffect(() => subscribeSlow(setWaking), [])

  return waking
}