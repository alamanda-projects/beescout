import { apiClient } from '@/lib/api/client'
import type { RuleCatalogItem, YamlValidationResult } from '@/types/rule_catalog'

export const getAllRules = async (): Promise<RuleCatalogItem[]> => {
  const res = await apiClient.get('/catalog/rules')
  return res.data
}

export const validateYaml = async (file: File): Promise<YamlValidationResult> => {
  const form = new FormData()
  form.append('file', file)
  const res = await apiClient.post('/contracts/validate-yaml', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export const importYaml = async (file: File) => {
  const form = new FormData()
  form.append('file', file)
  const res = await apiClient.post('/contracts/import-yaml', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}
