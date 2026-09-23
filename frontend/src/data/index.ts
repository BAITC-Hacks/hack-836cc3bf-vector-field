import { FixtureDataProvider } from './fixtureProvider'
import { HttpDataProvider } from './httpProvider'
import type { DataProvider } from './provider'

export * from './provider'
export * from './format'
export * from './labels'
export * from './limitations'
export { useAsyncData, type Async } from './useAsyncData'

/** Single switch between the fixture stage and the future API stage.
 *  Components never import a concrete provider — they take this instance. */
export function createDataProvider(): DataProvider {
  return import.meta.env.VITE_DATA_PROVIDER === 'fixture'
    ? new FixtureDataProvider()
    : new HttpDataProvider()
}
