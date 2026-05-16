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
