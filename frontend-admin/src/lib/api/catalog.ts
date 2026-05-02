// ─── Rule Catalog API client ──────────────────────────────────────────────────
// Letakkan file ini di: frontend-admin/src/lib/api/catalog.ts

import { apiClient as axios } from '@/lib/api/client'  // gunakan instance yang sudah ada
import type {
  RuleCatalogItem,
  RuleCatalogCreate,
  YamlValidationResult,
} from '@/types/rule_catalog'

// Ambil semua modul aturan
export const getAllRules = async (): Promise<RuleCatalogItem[]> => {
  const res = await axios.get('/catalog/rules')
  return res.data
}

// Ambil satu modul berdasarkan code
export const getRuleByCode = async (code: string): Promise<RuleCatalogItem> => {
  const res = await axios.get(`/catalog/rules/${code}`)
  return res.data
}

// Buat modul baru
export const createRule = async (payload: RuleCatalogCreate): Promise<RuleCatalogItem> => {
  const res = await axios.post('/catalog/rules', payload)
  return res.data
}

// Update modul kustom
export const updateRule = async (
  code: string,
  payload: Partial<RuleCatalogCreate>
): Promise<RuleCatalogItem> => {
  const res = await axios.patch(`/catalog/rules/${code}`, payload)
  return res.data
}

// Hapus modul kustom
export const deleteRule = async (code: string): Promise<void> => {
  await axios.delete(`/catalog/rules/${code}`)
}

// Validasi file YAML sebelum import
export const validateYaml = async (file: File): Promise<YamlValidationResult> => {
  const form = new FormData()
  form.append('file', file)
  const res = await axios.post('/contracts/validate-yaml', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

// Import kontrak dari file YAML (setelah validasi berhasil)
export const importYaml = async (file: File) => {
  const form = new FormData()
  form.append('file', file)
  const res = await axios.post('/contracts/import-yaml', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}
