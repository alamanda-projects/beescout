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

export async function getPendingApprovals(): Promise<ApprovalRecord[]> {
  const res = await apiClient.get('/approval/pending')
  return Array.isArray(res.data) ? res.data : []
}

export async function castVote(approvalId: string, vote: 'approved' | 'rejected', reason?: string) {
  const res = await apiClient.post(`/approval/${approvalId}/vote`, { vote, reason: reason || null })
  return res.data
}
