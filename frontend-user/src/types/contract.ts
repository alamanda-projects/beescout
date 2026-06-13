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
  // ADR-0004: dipakai untuk menentukan approver Producer/Consumer.
  // Hanya stakeholder ber-username yang aktif yang dihitung.
  username?: string
  date_in?: string
  date_out?: string
}

export interface Quality {
  code: string
  description?: string
  dimension?: string
  impact?: string
  severity?: string
  custom_properties?: Record<string, string>
}

export interface SLA {
  // Spec fields (required at write-time) — #102 PR-B slice 5
  availability_start?: number
  availability_end?: number
  availability_unit?: string   // 'h' | 'd'
  frequency?: number
  frequency_unit?: string      // 'm' | 'h' | 'd'
  frequency_cron?: string
  retention?: number
  retention_unit?: string
  // Legacy UI aliases — lenient on read for old contracts
  availability?: string
  cron?: string
}

export interface Metadata {
  version: string
  type: string
  name: string
  owner: string
  consumption_mode?: string
  // Lifecycle kontrak (#103, standard_version 0.5.0) — top-level, bukan di sla.
  effective_date?: string
  expiry_date?: string
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
  created_by?: string
  managers?: string[]
  approval_status?: string | null
  pending_changes?: Record<string, unknown> | null
  pending_by?: string | null
  approval_id?: string | null
}

export interface Vote {
  username: string
  vote: 'approved' | 'rejected'
  reason?: string | null
  voted_at?: string | null
}

// ADR-0005 — owner menggantikan steward; ketiga peran diturunkan dari
// metadata.stakeholders[role]. Admin/root tidak lagi otomatis ikut.
export type ApproverRole = 'owner' | 'producer' | 'consumer'

export const APPROVER_ROLE_LABELS: Record<ApproverRole, string> = {
  owner:    'Owner',
  producer: 'Producer',
  consumer: 'Consumer',
}

// Issue #69: pengajuan modul rule catalog dari user. Approval lama
// tanpa field 'type' default ke 'contract_change'.
export type ApprovalType = 'contract_change' | 'rule_catalog_create'

export interface ApprovalRecord {
  approval_id: string
  type?: ApprovalType
  target_id?: string | null                    // contract_number atau rule code
  contract_number?: string | null              // legacy untuk contract_change
  requested_by: string
  proposed_changes: Record<string, unknown>
  approvers: string[]
  // ADR-0005 — approver per peran. Kunci umum: owner/producer/consumer
  // (contract_change) atau steward (rule_catalog_create).
  approvers_by_role?: Record<string, string[]>
  fallback_roles?: string[]
  votes: Vote[]
  status: 'pending' | 'approved' | 'rejected'
  created_at?: string | null
  resolved_at?: string | null
}

export const CONTRACT_TYPE_LABELS: Record<string, string> = {
  dataset: 'Dataset',
  api: 'API',
  stream: 'Stream',
  report: 'Laporan',
  model: 'Model',
}

export const CONTRACT_TYPES     = ['dataset', 'api', 'stream', 'report', 'model'] as const
export const CONSUMPTION_MODES  = ['batch', 'streaming', 'real-time', 'on-demand'] as const
export const RETENTION_UNITS    = ['tahun', 'bulan', 'pekan', 'hari', 'jam'] as const
export const QUALITY_DIMENSIONS = [
  { value: 'completeness', label: 'Completeness' },
  { value: 'validity',     label: 'Validity' },
  { value: 'accuracy',     label: 'Accuracy' },
] as const

export interface StakeholderRoleItem { value: string; label: string }
export interface StakeholderRoleGroup { group: string; items: StakeholderRoleItem[] }

// Role di kontrak = fungsi user terhadap kontrak ini (BUKAN job title).
// Spec BeeScout: enum closed 4 nilai (data-contract/docs/README.md line 94).
// 1 user dengan job title sama bisa beda role di kontrak berbeda. Label
// dipilih untuk menjelaskan fungsi, bukan profesi. Lihat docs/glossary.md.
export const STAKEHOLDER_ROLE_GROUPS: StakeholderRoleGroup[] = [
  {
    group: 'Fungsi di Kontrak',
    items: [
      { value: 'owner',    label: 'Pemilik — kewenangan penuh terkait kontrak' },
      { value: 'producer', label: 'Produser — menyediakan/menghasilkan data' },
      { value: 'consumer', label: 'Konsumen — menggunakan data dari kontrak' },
      { value: 'reviewer', label: 'Pengawas — tata kelola / audit (Governance, GRC, Security)' },
    ],
  },
]

export const STAKEHOLDER_ROLES: StakeholderRoleItem[] = STAKEHOLDER_ROLE_GROUPS.flatMap(g => g.items)

export function getStakeholderRoleLabel(value: string): string {
  return STAKEHOLDER_ROLES.find(r => r.value === value)?.label ?? value
}
