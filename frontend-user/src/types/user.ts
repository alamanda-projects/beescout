// #91 (PR-B dari #75): alias legacy 'user' sudah dihapus — value resmi
// tinggal 'business_user'. `type` di sini = account type (user vs sa),
// beda dari role.
export interface User {
  client_id: string
  group_access: 'root' | 'admin' | 'business_user' | 'developer'
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
  business_user: 'Business User',
  developer: 'Developer',
}

// #91: alias lama `user` dihapus — cek langsung nilai resmi.
export const isBusinessUser = (role?: string): boolean =>
  role === 'business_user'
