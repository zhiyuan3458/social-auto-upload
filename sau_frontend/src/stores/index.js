import { createPinia } from 'pinia'
import { useUserStore } from './user'
import { useAccountStore } from './account'
import { useAppStore } from './app'
import { usePublishPresetStore } from './publishPreset'

const pinia = createPinia()

export default pinia
export { useUserStore, useAccountStore, useAppStore, usePublishPresetStore }