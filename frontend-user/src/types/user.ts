// `group_access: 'user'` masih diterima selama window migrasi (#75 PR-A,
// dual-accept). PR-B (#91) menjalankan migration + menghapus alias.
// `type` di sini = account type (user vs sa), beda dari role.
export interface User {
  client_id: string
  group_access: 'root' | 'admin' | 'user' | 'business_user' | 'developer'
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
  user: 'Business User',          // legacy alias — label disamakan
  business_user: 'Business User',
  developer: 'Developer',
}

// #75 PR-A: helper untuk cek role business — terima alias lama `user`.
export const isBusinessUser = (role?: string): boolean =>
  role === 'user' || role === 'business_user'
