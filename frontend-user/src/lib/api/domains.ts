import { apiClient } from '@/lib/api/client'

export interface DomainBasic { name: string; label: string }

// Direktori ringan utk dropdown Pemilik kontrak (#73) — bisa dipanggil semua role.
// Backend: GET /domain/basic (require_any). Pakai ini bila hanya butuh slug + label.
export async function getDomainsBasic(): Promise<DomainBasic[]> {
  const res = await apiClient.get('/domain/basic')
  return Array.isArray(res.data) ? res.data : []
}
