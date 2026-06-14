import { apiClient } from './client'
import type { Contract, ApprovalRecord } from '@/types/contract'

export async function getContracts(contractNumber?: string): Promise<Contract[]> {
  try {
    const params = contractNumber ? { contract_number: contractNumber } : undefined
    const res = await apiClient.get('/datacontract/filter', { params })
    const data = res.data
    if (Array.isArray(data)) return data
    if (data && typeof data === 'object') return [data as Contract]
    return []
  } catch {
    return []
  }
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

export async function getContractByNumber(contractNumber: string): Promise<Contract | null> {
  try {
    const res = await apiClient.get('/datacontract/filter', {
      params: { contract_number: contractNumber },
    })
    const data = res.data
    if (Array.isArray(data)) return data[0] ?? null
    if (data && typeof data === 'object') return data as Contract
    return null
  } catch {
    return null
  }
}

export async function getContractModel(contractNumber: string) {
  const res = await apiClient.get('/datacontract/model/filter', {
    params: { contract_number: contractNumber },
  })
  return res.data
}

export async function getContractPorts(contractNumber: string) {
  const res = await apiClient.get('/datacontract/ports/filter', {
    params: { contract_number: contractNumber },
  })
  return res.data
}

export async function getContractExamples(contractNumber: string) {
  const res = await apiClient.get('/datacontract/examples/filter', {
    params: { contract_number: contractNumber },
  })
  return res.data
}

export async function getMyApprovals(): Promise<ApprovalRecord[]> {
  const res = await apiClient.get('/approval/mine')
  return Array.isArray(res.data) ? res.data : []
}

export interface UserBasic { username: string; name: string }

// Direktori ringan utk dropdown stakeholder — bisa dipanggil semua role.
// Backend: GET /user/basic (require_any).
export async function getUsersBasic(): Promise<UserBasic[]> {
  const res = await apiClient.get('/user/basic')
  return Array.isArray(res.data) ? res.data : []
}

export async function updateContract(contractNumber: string, data: unknown) {
  const res = await apiClient.put('/datacontract/update', data, {
    params: { contract_number: contractNumber },
  })
  return res.data
}

export async function addContract(data: unknown) {
  const res = await apiClient.post('/datacontract/add', data)
  return res.data
}

export async function generateContractNumber(): Promise<string> {
  const res = await apiClient.get('/datacontract/gencn')
  return res.data.contract_number
}

export async function importYaml(file: File) {
  const form = new FormData()
  form.append('file', file)
  const res = await apiClient.post('/datacontract/import-yaml', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}
