export interface User {
  client_id: string
  group_access: 'root' | 'admin' | 'user' | 'developer'
  data_domain: string
  is_active: boolean
  type: 'user' | 'sa'
}

export interface SAKey {
  client_id: string
  generated_at: string
  is_active: boolean
  expire_at: string
}

export const ROLE_LABELS: Record<string, string> = {
  root: 'Super Admin',
  admin: 'Admin',
  user: 'Pengguna',
  developer: 'Developer',
}

export const ADMIN_ROLES = ['admin', 'root'] as const
