import type { FormEvent, ReactNode } from 'react'
import type { Gid } from '@shared/contracts'

interface Props {
  value: string
  onValueChange(value: string): void
  onSearch(gid: Gid): void
  validationError: string | null
  feedback: ReactNode
}

/** Exact gid lookup. The value is treated as an opaque decimal string:
 *  no Number(), no parseInt(), no trimming beyond whitespace. */
export function SearchBox({ value, onValueChange, onSearch, validationError, feedback }: Props) {
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
      <h2 className="panel-title">Поиск по gid</h2>
      <form className="search" onSubmit={submit}>
        <input
          className="search-input"
          value={value}
          onChange={(event) => onValueChange(event.target.value)}
          placeholder="точный gid, например 900000000000000001"
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
        Только точное совпадение по полному gid — строке из десятичных цифр. Сейчас доступна fixture-коллекция;
        полный dataset станет доступен после подключения <code>GET /api/entities/{'{gid}'}</code>.
      </p>
      {validationError ? <p className="field-error">{validationError}</p> : null}
      {feedback}
    </section>
  )
}
