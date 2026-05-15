// ─── Rule Catalog Types ───────────────────────────────────────────────────────

export type ParamType   = 'text' | 'number' | 'select' | 'multi' | 'date'
export type LayerType   = 'dataset' | 'column' | 'both'
export type DimensionType = 'completeness' | 'validity' | 'accuracy' | 'security'
export type ImpactType   = 'operational' | 'financial' | 'regulatory' | 'reputational'
export type SeverityType = 'low' | 'medium' | 'high'

export interface RuleParamOption {
  value: string
  label: string
}

export interface RuleParam {
  key: string
  label: string
  type: ParamType
  required: boolean
  options?: RuleParamOption[]   // untuk type=select/multi
  min_value?: number            // validasi angka
  max_value?: number
  hint?: string
}

export interface RuleCatalogItem {
  code: string
  label: string
  description?: string
  layer: LayerType
  dimension: DimensionType
  sentence_template: string
  params: RuleParam[]
  is_builtin: boolean
  is_active: boolean
}

export interface RuleCatalogCreate {
  code: string
  label: string
  description?: string
  layer: LayerType
  dimension: DimensionType
  sentence_template: string
  params: RuleParam[]
}

// ─── Quality rule (yang disimpan di kontrak) ──────────────────────────────────

export interface QualityCustomProp {
  property: string
  value: string
}

export interface QualityRule {
  code: string
  description?: string
  dimension?: string
  impact?: string    // operational | financial | regulatory | reputational
  severity?: string  // low | medium | high
  custom_properties?: QualityCustomProp[]
}

// ─── YAML import ──────────────────────────────────────────────────────────────

export interface YamlValidationError {
  field?: string
  line?: number
  message: string
  suggestion?: string
}

export interface YamlImportSummary {
  contract_name: string
  owner: string
  type: string
  version: string
  columns: number
  dataset_quality_rules: number
  column_quality_rules: number
  stakeholders: number
  has_contract_number: boolean
  raw: Record<string, unknown>
}

export interface YamlValidationResult {
  valid: boolean
  layer: 'yaml_syntax' | 'odcs_schema' | 'passed'
  errors?: YamlValidationError[]
  warnings?: YamlValidationError[]
  suggestions?: string[]
  summary?: YamlImportSummary
}

// ─── UI helpers ───────────────────────────────────────────────────────────────

export const DIMENSION_LABELS: Record<DimensionType, string> = {
  completeness: 'Kelengkapan',
  validity:     'Keabsahan',
  accuracy:     'Akurasi',
  security:     'Keamanan',
}

export const IMPACT_TYPE_LABELS: Record<ImpactType, string> = {
  operational:  'Operasional',
  financial:    'Finansial',
  regulatory:   'Regulasi',
  reputational: 'Reputasi',
}

export const SEVERITY_LABELS: Record<SeverityType, string> = {
  low:    'Rendah',
  medium: 'Sedang',
  high:   'Tinggi',
}

export const SEVERITY_BIZ_LABELS: Record<SeverityType, string> = {
  low:    'Tidak terlalu kritis',
  medium: 'Cukup penting',
  high:   'Sangat penting',
}

// backward-compat aliases — pakai untuk display data lama yang belum dimigrate
export const IMPACT_LABELS = IMPACT_TYPE_LABELS
export const IMPACT_BIZ_LABELS: Record<string, string> = {
  ...SEVERITY_BIZ_LABELS,
  operational:  'Operasional',
  financial:    'Finansial',
  regulatory:   'Regulasi',
  reputational: 'Reputasi',
}

export const LAYER_LABELS: Record<LayerType, string> = {
  dataset: 'Keseluruhan Dataset',
  column:  'Per Kolom',
  both:    'Dataset & Kolom',
}
