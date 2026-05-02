export interface ContractDescription {
  purpose?: string
  usage?: string
}

export interface Consumer {
  name: string
  use_case?: string
}

export interface Stakeholder {
  name: string
  email?: string
  role: string
  date_in?: string
  date_out?: string
}

export interface Quality {
  code: string
  description?: string
  dimension?: string
  impact?: string
  custom_properties?: Record<string, string>
}

export interface SLA {
  availability?: string
  frequency?: string
  retention?: string
  cron?: string
}

export interface Metadata {
  version: string
  type: string
  name: string
  owner: string
  consumption_mode?: string
  description?: ContractDescription
  consumer?: Consumer[]
  stakeholders?: Stakeholder[]
  quality?: Quality[]
  sla?: SLA
  prev_contract?: string
  contract_reference?: string[]
}

export interface ModelColumn {
  column: string
  business_name?: string
  logical_type?: string
  physical_type?: string
  is_primary?: boolean
  is_nullable?: boolean
  is_partition?: boolean
  is_clustered?: boolean
  is_pii?: boolean
  is_audit?: boolean
  is_mandatory?: boolean
  description?: string
  quality?: Quality[]
  sample_value?: string[]
  tags?: string[]
}

export interface PortProperty {
  name: string
  value: string
}

export interface Port {
  object: string
  properties?: PortProperty[]
}

export interface Examples {
  type?: string
  data?: unknown
}

export interface Contract {
  standard_version: string
  contract_number: string
  metadata: Metadata
  model?: ModelColumn[]
  ports?: Port[]
  examples?: Examples
}

export const CONTRACT_TYPE_LABELS: Record<string, string> = {
  dataset: 'Dataset',
  api: 'API',
  stream: 'Stream',
  report: 'Laporan',
  model: 'Model',
}
