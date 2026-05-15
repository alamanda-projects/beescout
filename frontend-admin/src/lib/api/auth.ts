import { apiClient } from './client'
import type { User, SAKey } from '@/types/user'

export async function login(username: string, password: string) {
  const res = await apiClient.post('/login', { username, password })
  return res.data
}

export async function getSetupStatus(): Promise<{ setup_complete: boolean }> {
  const res = await apiClient.get('/setup/status')
  return res.data
}

export async function createRootAccount(data: {
  username: string
  password: string
  name: string
  data_domain: string
  import_sample_contracts: boolean
  import_catalog_rules: boolean
}) {
  const res = await apiClient.post('/setup', {
    ...data,
    group_access: 'root',
    is_active: true,
  })
  return res.data
}

export async function logout() {
  await apiClient.post('/logout')
}

export async function getMe(): Promise<User> {
  const res = await apiClient.get('/user/me')
  return res.data
}

export async function getSAKeys(): Promise<{ sakeys: SAKey[] }> {
  const res = await apiClient.get('/sakey/lists')
  return res.data
}
