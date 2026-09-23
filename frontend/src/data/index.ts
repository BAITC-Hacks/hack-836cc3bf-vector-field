import { FixtureDataProvider } from './fixtureProvider'
import { HttpDataProvider } from './httpProvider'
import type { DataProvider } from './provider'

export * from './provider'
export * from './format'
export * from './labels'
export * from './limitations'
export { useAsyncData, type Async } from './useAsyncData'

/** Live API by default; synthetic fixtures require an explicit switch. */
export function createDataProvider(): DataProvider {
  return import.meta.env.VITE_DATA_PROVIDER === 'fixture'
    ? new FixtureDataProvider()
    : new HttpDataProvider()
}
