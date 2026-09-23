import { useEffect, useState, type DependencyList } from 'react'
import { toProviderError, type ProviderError } from './provider'

export type Async<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'ready'; data: T }
  | { status: 'error'; error: ProviderError }

/** Minimal loading/error/ready wrapper. No state manager — one screen, one hook. */
export function useAsyncData<T>(loader: () => Promise<T>, deps: DependencyList): Async<T> {
  const [state, setState] = useState<Async<T>>({ status: 'idle' })

  useEffect(() => {
    let cancelled = false
    setState({ status: 'loading' })
    loader().then(
      (data) => {
        if (!cancelled) setState({ status: 'ready', data })
      },
      (error: unknown) => {
        if (!cancelled) setState({ status: 'error', error: toProviderError(error) })
      },
    )
    return () => {
      cancelled = true
    }
    // The caller passes its own dependency list; the loader closes over them.
  }, deps)

  return state
}
