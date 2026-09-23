import type { ReactNode } from 'react'
import type { ProviderError } from '../data/provider'

export function LoadingBlock({ label = 'Загрузка…' }: { label?: string }) {
  return (
    <div className="state state-loading" role="status" aria-live="polite">
      <span className="state-spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}

interface StateBlockProps {
  title: string
  error: ProviderError
  hint?: ReactNode
}

/** ENTITY_NOT_FOUND is a data-availability state, not a crash: it renders as a
 *  neutral "unavailable" block. Everything else is a real error. */
export function StateBlock({ title, error, hint }: StateBlockProps) {
  const unavailable = error.code === 'ENTITY_NOT_FOUND'
  return (
    <div
      className={`state ${unavailable ? 'state-unavailable' : 'state-error'}`}
      role={unavailable ? 'status' : 'alert'}
    >
      <div className="state-head">
        <span className="state-title">{title}</span>
        <code className="state-code">{error.code}</code>
      </div>
      <p className="state-message">{error.message}</p>
      {hint ? <div className="state-hint">{hint}</div> : null}
    </div>
  )
}

// Backwards-compatible descriptive name used by the panels.
export const ErrorBlock = StateBlock

export function EmptyBlock({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="state state-empty" role="status">
      <div className="state-title">{title}</div>
      {children ? <p className="state-message">{children}</p> : null}
    </div>
  )
}
