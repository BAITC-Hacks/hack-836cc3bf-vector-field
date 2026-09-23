import type { FormEvent, ReactNode } from 'react'
import type { Gid } from '@shared/contracts'

interface Props {
  mode: 'fixture' | 'live'
  value: string
  onValueChange(value: string): void
  onSearch(gid: Gid): void
  validationError: string | null
  feedback: ReactNode
}

/** Exact gid lookup. The value is treated as an opaque decimal string:
 *  no Number(), no parseInt(), no trimming beyond whitespace. */
export function SearchBox({ mode, value, onValueChange, onSearch, validationError, feedback }: Props) {
  function submit(event: FormEvent) {
    event.preventDefault()
    const gid = value.trim()
    if (gid === '') {
      onSearch('')
      return
    }
    onSearch(gid)
  }

  return (
    <section className="panel">
      <h2 className="panel-title">Найти узел по GID</h2>
      <form className="search" onSubmit={submit}>
        <input
          className="search-input"
          value={value}
          onChange={(event) => onValueChange(event.target.value)}
          placeholder={mode === 'fixture' ? '900000000000000001' : 'Полный идентификатор клиента'}
          spellCheck={false}
          autoComplete="off"
          inputMode="numeric"
          aria-label="Точный gid"
        />
        <button className="btn" type="submit">
          Найти
        </button>
      </form>
      <p className="hint">
        {mode === 'live' ? 'Поиск по всей сети, включая узлы вне очереди.' : 'Поиск в учебном наборе.'} Вставьте полный GID.
      </p>
      {validationError ? <p className="field-error">{validationError}</p> : null}
      {feedback}
    </section>
  )
}
