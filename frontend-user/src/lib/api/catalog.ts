import { apiClient } from '@/lib/api/client'
import type { RuleCatalogCreate, RuleCatalogItem, YamlValidationResult } from '@/types/rule_catalog'

export const getAllRules = async (): Promise<RuleCatalogItem[]> => {
  const res = await apiClient.get('/catalog/rules')
  return res.data
}

// Ajukan modul aturan baru. Backend mendeteksi role:
// - admin/root: langsung tersimpan & mengembalikan RuleCatalogItem.
// - user/developer: masuk approval, mengembalikan { approval_id, status: 'pending', ... }.
// Frontend menangani kedua bentuk respons.
export interface CatalogProposalResponse {
  message: string
  approval_id: string
  approvers: string[]
  rule_code: string
  status: 'pending'
}

export const createRule = async (
  payload: RuleCatalogCreate,
): Promise<RuleCatalogItem | CatalogProposalResponse> => {
  const res = await apiClient.post('/catalog/rules', payload)
  return res.data
}

export const validateYaml = async (
  file: File,
  format: 'beescout' | 'odcs' = 'beescout',
): Promise<YamlValidationResult> => {
  const form = new FormData()
  form.append('file', file)
  const res = await apiClient.post('/contracts/validate-yaml', form, {
    params: { format },
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

// format='odcs' → konversi ODCS→BeeScout dulu di backend (#100).
export const importYaml = async (file: File, format: 'beescout' | 'odcs' = 'beescout') => {
  const form = new FormData()
  form.append('file', file)
  const res = await apiClient.post('/contracts/import-yaml', form, {
    params: { format },
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}
