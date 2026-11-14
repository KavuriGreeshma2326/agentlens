import { useEffect, useState } from 'react'

/** The current URL hash (for example "#/runs/5"), kept up to date as it changes. */
export function useHash(): string {
  const [hash, setHash] = useState(window.location.hash)

  useEffect(() => {
    const onChange = () => setHash(window.location.hash)
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])

  return hash
}