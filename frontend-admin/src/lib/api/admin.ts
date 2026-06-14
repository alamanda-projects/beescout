import { apiClient } from './client'
import type { Contract, ApprovalRecord } from '@/types/contract'

export async function getAllContracts(): Promise<Contract[]> {
  const res = await apiClient.get('/datacontract/lists')
  const data = res.data
  if (Array.isArray(data)) return data
  if (data && typeof data === 'object') return [data as Contract]
  return []
}

export async function getContractByNumber(cn: string): Promise<Contract | null> {
  try {
    const res = await apiClient.get('/datacontract/filter', { params: { contract_number: cn } })
    const data = res.data
    if (Array.isArray(data)) return data[0] ?? null
    if (data && typeof data === 'object') return data as Contract
    return null
  } catch {
    return null
  }
}

export async function addContract(data: unknown) {
  const res = await apiClient.post('/datacontract/add', data)
  return res.data
}

// Export kontrak ke ODCS YAML (#101). Unduh via blob — endpoint mengembalikan
// Content-Disposition attachment; cookie auth ikut karena withCredentials.
export async function exportContractOdcs(cn: string): Promise<void> {
  const res = await apiClient.get(`/datacontract/${encodeURIComponent(cn)}/export`, {
    params: { format: 'odcs' },
    responseType: 'blob',
  })
  const url = URL.createObjectURL(res.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${cn}.odcs.yaml`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export async function generateContractNumber(): Promise<string> {
  const res = await apiClient.get('/datacontract/gencn')
  return res.data.contract_number
}

export async function updateContract(contractNumber: string, data: unknown) {
  const res = await apiClient.put('/datacontract/update', data, {
    params: { contract_number: contractNumber },
  })
  return res.data
}

export interface UserRecord {
  username: string
  name: string
  group_access: string
  data_domain: string
  is_active: boolean
  created_at?: string
}

export async function getUsers(): Promise<UserRecord[]> {
  const res = await apiClient.get('/user/lists')
  return Array.isArray(res.data) ? res.data : []
}

export interface UserBasic { username: string; name: string }

// Direktori ringan utk dropdown stakeholder — bisa dipanggil semua role.
// Backend: GET /user/basic (require_any). Pakai ini di tempat-tempat yang
// hanya butuh username + nama tampilan.
export async function getUsersBasic(): Promise<UserBasic[]> {
  const res = await apiClient.get('/user/basic')
  return Array.isArray(res.data) ? res.data : []
}

export async function createUser(data: {
  username: string
  password: string
  name: string
  group_access: string
  data_domain: string
  is_active: boolean
}) {
  const res = await apiClient.post('/user/create', data)
  return res.data
}

export async function updateUser(username: string, data: {
  name?: string
  group_access?: string
  data_domain?: string
  is_active?: boolean
  password?: string
}) {
  const res = await apiClient.patch(`/user/${username}`, data)
  return res.data
}

export async function deleteUser(username: string) {
  const res = await apiClient.delete(`/user/${username}`)
  return res.data
}

export async function getPendingApprovals(): Promise<ApprovalRecord[]> {
  const res = await apiClient.get('/approval/pending')
  return Array.isArray(res.data) ? res.data : []
}

export async function castVote(approvalId: string, vote: 'approved' | 'rejected', reason?: string) {
  const res = await apiClient.post(`/approval/${approvalId}/vote`, { vote, reason: reason || null })
  return res.data
}

// ── Domain management ─────────────────────────────────────────────────────────

export interface DomainRecord {
  name: string
  label: string
  description?: string
  is_active: boolean
  // Domain default ('root', 'admin') yang di-seed /setup (#74). Tidak boleh
  // dinonaktifkan / dihapus — UI menyembunyikan kontrol terkait.
  is_default?: boolean
  user_count?: number
  created_at?: string
}

export async function getDomains(includeInactive = false): Promise<DomainRecord[]> {
  const res = await apiClient.get('/domain/lists', {
    params: includeInactive ? { include_inactive: true } : {},
  })
  return Array.isArray(res.data) ? res.data : []
}

export interface DomainBasic { name: string; label: string }

// Direktori ringan utk dropdown Pemilik kontrak (#73) — bisa dipanggil semua role.
// Backend: GET /domain/basic (require_any). Pakai ini bila hanya butuh slug + label.
export async function getDomainsBasic(): Promise<DomainBasic[]> {
  const res = await apiClient.get('/domain/basic')
  return Array.isArray(res.data) ? res.data : []
}

export async function createDomain(data: { name: string; label: string; description?: string }) {
  const res = await apiClient.post('/domain/create', data)
  return res.data
}

export async function updateDomain(
  name: string,
  data: { label?: string; description?: string; is_active?: boolean },
) {
  const res = await apiClient.patch(`/domain/${name}`, data)
  return res.data
}

export async function deactivateDomain(name: string) {
  const res = await apiClient.delete(`/domain/${name}`)
  return res.data
}
