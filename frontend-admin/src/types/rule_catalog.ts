// ─── Rule Catalog Types ───────────────────────────────────────────────────────

export type ParamType   = 'text' | 'number' | 'select' | 'multi' | 'date'
export type LayerType   = 'dataset' | 'column' | 'both'
export type DimensionType = 'completeness' | 'validity' | 'accuracy' | 'security'
export type ImpactType  = 'operational' | 'high' | 'low'

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
  value: string | number
}

export interface QualityRule {
  code: string
  description?: string
  dimension?: string
  impact?: string
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

export const IMPACT_LABELS: Record<ImpactType, string> = {
  operational: 'Operasional',
  high:        'Tinggi',
  low:         'Rendah',
}

export const IMPACT_BIZ_LABELS: Record<string, string> = {
  operational: 'Cukup penting',
  high:        'Penting sekali',
  low:         'Rendah',
}

export const LAYER_LABELS: Record<LayerType, string> = {
  dataset: 'Keseluruhan Dataset',
  column:  'Per Kolom',
  both:    'Dataset & Kolom',
}
