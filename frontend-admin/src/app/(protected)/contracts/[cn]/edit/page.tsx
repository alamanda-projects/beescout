'use client'

import { useState, useEffect, useRef } from 'react'
import { useForm, useFieldArray, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { requiredEmailField, requiredString, requiredInt, cronField, enumField } from '@/lib/zod-helpers'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getContractByNumber, updateContract, getUsersBasic, getDomainsBasic } from '@/lib/api/admin'
import { getMe } from '@/lib/api/auth'
import { ImportYamlButton } from '@/components/quality/ImportYamlModal'
import QualityRulesEditor from '@/components/quality/QualityRulesEditor'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { toast } from 'sonner'
import { Plus, Trash2, Loader2, ArrowLeft, Save, Info } from 'lucide-react'
import { CONTRACT_TYPES, CONSUMPTION_MODES, STAKEHOLDER_ROLE_GROUPS, STAKEHOLDER_ROLE_VALUES, LEGACY_STAKEHOLDER_ROLES, RETENTION_UNITS, QUALITY_DIMENSIONS } from '@/types/contract'
import { isBusinessUser } from '@/types/user'
import { COLUMN_FLAG_HELP, DATA_TYPE_HELP } from '@/lib/field-help'

const schema = z.object({
  standard_version: z.string().min(1, 'Wajib diisi'),
  contract_number: z.string().min(1, 'Wajib diisi'),
  metadata: z.object({
    version: z.string().min(1, 'Wajib diisi'),
    type: z.string().min(1, 'Pilih tipe kontrak'),
    name: z.string().min(1, 'Wajib diisi'),
    owner: z.string().min(1, 'Wajib diisi'),
    consumption_mode: z.string().optional(),
    // Lifecycle kontrak (#103) — top-level, bukan di sla.
    effective_date: z.string().min(1, 'Tanggal mulai wajib diisi'),
    expiry_date: z.string().min(1, 'Tanggal berakhir wajib diisi'),
    // #102 PR-B: spec-YES → wajib (purpose: alasan dataset ada; usage: cara
    // pakai). Enforcement berlapis (FE zod + write-time check di main.py).
    description: z.object({
      purpose: requiredString('Tujuan wajib diisi'),
      usage: requiredString('Cara penggunaan wajib diisi'),
    }),
    // #102 PR-B slice 5: SLA spec-YES → wajib. Pydantic tetap Optional.
    sla: z.object({
      availability_start: requiredInt('Jam mulai wajib diisi', 0, 23),
      availability_end: requiredInt('Jam selesai wajib diisi', 0, 23),
      availability_unit: z.enum(['h', 'd'], { required_error: 'Unit wajib dipilih' }),
      frequency: requiredInt('Interval frekuensi wajib diisi', 0),
      frequency_unit: z.enum(['m', 'h', 'd'], { required_error: 'Unit wajib dipilih' }),
      frequency_cron: cronField(),
      retention: z.string().min(1, 'Retensi data wajib diisi'),
    }),
    // ADR-0007: minimal 1 stakeholder dengan role consumer/producer wajib
    // — sama dengan create. Mencegah workaround "create lalu hapus
    // stakeholder via edit". Backend juga validate di PUT /update.
    stakeholders: z.array(z.object({
      name: z.string().min(1, 'Nama wajib diisi'),
      role: enumField(STAKEHOLDER_ROLE_VALUES, { legacy: LEGACY_STAKEHOLDER_ROLES, emptyMsg: 'Peran wajib diisi', invalidMsg: 'Peran tidak valid' }),
      email: requiredEmailField(),
      username: z.string().optional(),    // ADR-0004
      // #114 T1.3 — date_in wajib di spec; pre-fill akan auto-stamp today
      // untuk kontrak legacy yang stakeholder-nya belum punya.
      date_in: z.string().min(1, 'Tanggal mulai wajib diisi'),
      date_out: z.string().optional(),
    }).refine(
      // #114: tanggal berakhir stakeholder tidak boleh sebelum tanggal mulai.
      (s) => !s.date_out || s.date_out >= s.date_in,
      { message: 'Tanggal berakhir harus sama atau setelah tanggal mulai', path: ['date_out'] },
    ))
      .min(1, 'Minimal 1 pemangku kepentingan wajib ditambahkan')
      .refine(
        (arr) => arr.some((s) => s.role === 'consumer' || s.role === 'producer'),
        { message: 'Minimal 1 pemangku kepentingan harus berperan sebagai consumer atau producer agar tim terkait dapat melihat kontrak' }
      ),
    // Hot-fix #92: konsumen team di-track di form state supaya auto-sync
    // dari stakeholder consumer bisa push data_domain-nya. Edit page juga
    // perlu agar nilai existing tidak silent-drop saat submit.
    consumer: z.array(z.object({
      name: requiredString('Nama konsumen wajib diisi'),
      use_case: z.string().optional(),
    })).optional(),
    quality: z.array(z.object({
      code: z.string().min(1, 'Kode wajib diisi'),
      dimension: z.string().optional(),
      description: z.string().optional(),
      impact: z.string().optional(),
      severity: z.string().optional(),
    })).optional(),
  }).refine(
    // #114: tanggal berakhir tidak boleh sebelum tanggal mulai (ISO → bandingkan string).
    (m) => !m.effective_date || !m.expiry_date || m.expiry_date >= m.effective_date,
    { message: 'Tanggal berakhir harus sama atau setelah tanggal mulai', path: ['expiry_date'] },
  ),
  model: z.array(z.object({
    column: z.string().min(1, 'Nama kolom wajib diisi'),
    business_name: z.string().optional(),
    logical_type: requiredString('Tipe Data Bisnis wajib diisi'),
    physical_type: requiredString('Tipe Data Teknis wajib diisi'),
    description: requiredString('Deskripsi kolom wajib diisi'),
    is_primary: z.boolean().optional(),
    is_nullable: z.boolean().optional(),
    is_partition: z.boolean().optional(),
    is_clustered: z.boolean().optional(),
    is_pii: z.boolean().optional(),
    is_audit: z.boolean().optional(),
    is_mandatory: z.boolean().optional(),
  })).optional(),
  // Koneksi opsional — field lenient supaya baris kosong tidak memblokir
  // submit; dibersihkan di onSubmit.
  ports: z.array(z.object({
    object: z.string().optional(),
    properties: z.array(z.object({
      name: z.string().optional(),
      value: z.string().optional(),
    })).optional(),
  })).optional(),
})

type FormData = z.infer<typeof schema>

const SECTIONS = ['Informasi Dasar', 'SLA & Pemangku', 'Struktur Data', 'Koneksi (Port)']

export default function EditContractPage() {
  const { cn } = useParams<{ cn: string }>()
  const router = useRouter()
  const queryClient = useQueryClient()
  const [step, setStep] = useState(0)
  const [activeSection, setActiveSection] = useState(0)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { data: user } = useQuery({ queryKey: ['me'], queryFn: getMe })
  const userRole = user?.group_access ?? 'user'
  // Direktori user utk dropdown stakeholder (ADR-0004).
  const { data: userOptions = [] } = useQuery({ queryKey: ['users-basic'], queryFn: getUsersBasic })
  // Katalog domain untuk dropdown Pemilik (#73).
  const { data: domainOptions = [] } = useQuery({ queryKey: ['domains-basic'], queryFn: getDomainsBasic })

  const { data: contract, isLoading } = useQuery({
    queryKey: ['contract', cn],
    queryFn: () => getContractByNumber(cn),
    enabled: !!cn,
  })

  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      standard_version: '1.0',
      contract_number: '',
      metadata: { version: '', type: '', name: '', owner: '', consumption_mode: '', effective_date: '', expiry_date: '', description: { purpose: '', usage: '' }, sla: { availability_start: undefined as any, availability_end: undefined as any, availability_unit: 'h' as 'h' | 'd', frequency: undefined as any, frequency_unit: 'h' as 'm' | 'h' | 'd', frequency_cron: '', retention: '' }, stakeholders: [], quality: [] },
      model: [],
      ports: [],
    },
  })

  // Pre-fill form HANYA SEKALI saat kontrak pertama dimuat. Tanpa guard ini,
  // refetch react-query (referensi `contract` berubah) memicu form.reset ulang
  // → menimpa form & menghapus field non-register (issue: type kembali kosong).
  const hydratedRef = useRef(false)
  useEffect(() => {
    if (!contract || hydratedRef.current) return
    hydratedRef.current = true
    const m = contract.metadata ?? {}

    // Parse retention string e.g. "2 tahun" → value + unit
    const retentionStr = String((m.sla as any)?.retention ?? '')
    const retentionMatch = retentionStr.match(/^(\d+)\s+(tahun|bulan|pekan|hari|jam)$/)
    if (retentionMatch) {
      setRetentionValue(retentionMatch[1])
      setRetentionUnit(retentionMatch[2])
    } else if (retentionStr) {
      setRetentionValue(retentionStr)
    }

    // #103: terima top-level (new shape) atau legacy sla.effective_date/end_of_contract,
    // ambil 10 char pertama agar cocok dengan <input type="date"> (YYYY-MM-DD).
    const toDateInput = (v: unknown): string =>
      typeof v === 'string' && v.length >= 10 ? v.slice(0, 10) : ''
    const effectiveRaw = (m as any).effective_date ?? (m.sla as any)?.effective_date
    const expiryRaw = (m as any).expiry_date ?? (m.sla as any)?.end_of_contract

    form.reset({
      standard_version: contract.standard_version ?? '1.0',
      contract_number: contract.contract_number,
      metadata: {
        version: m.version ?? '',
        type: m.type ?? '',
        name: m.name ?? '',
        owner: m.owner ?? '',
        consumption_mode: m.consumption_mode ?? '',
        effective_date: toDateInput(effectiveRaw),
        expiry_date: toDateInput(expiryRaw),
        description: {
          purpose: m.description?.purpose ?? '',
          usage: (m.description as any)?.usage ?? '',
        },
        sla: {
          availability_start: (m.sla as any)?.availability_start ?? undefined as any,
          availability_end: (m.sla as any)?.availability_end ?? undefined as any,
          availability_unit: ((m.sla as any)?.availability_unit ?? 'h') as 'h' | 'd',
          frequency: (m.sla as any)?.frequency ?? undefined as any,
          frequency_unit: ((m.sla as any)?.frequency_unit ?? 'h') as 'm' | 'h' | 'd',
          frequency_cron: (m.sla as any)?.frequency_cron ?? (m.sla as any)?.cron ?? '',
          retention: retentionStr,
        },
        stakeholders: (m.stakeholders ?? []).map((s: any) => ({
          name: s.name ?? '',
          role: s.role ?? '',
          email: s.email ?? '',
          username: s.username ?? undefined,
          // #114 T1.3 — normalize ISO timestamp ke YYYY-MM-DD untuk <input type="date">.
          // Kontrak legacy yang stakeholder belum punya date_in: stamp today
          // supaya zod required tidak block, & user bisa over-ride sebelum save.
          date_in: toDateInput(s.date_in) || new Date().toISOString().slice(0, 10),
          date_out: toDateInput(s.date_out),
        })),
        // Round-trip metadata.consumer[] (field documentary use_case, ADR-0007)
        // supaya nilai existing tidak hilang silent saat submit.
        consumer: ((m as any).consumer ?? []).map((c: any) => ({
          name: c.name ?? '',
          use_case: c.use_case ?? '',
        })),
        quality: ((m as any).quality ?? []).map((q: any) => ({
          code: q.code ?? '',
          dimension: q.dimension ?? 'completeness',
          description: q.description ?? '',
          impact: q.impact ?? '',
          severity: q.severity ?? '',
        })),
      },
      model: (contract.model ?? []).map((col: any) => ({
        column: col.column ?? '',
        business_name: col.business_name ?? '',
        logical_type: col.logical_type ?? '',
        physical_type: col.physical_type ?? '',
        description: col.description ?? '',
        is_primary: !!col.is_primary,
        is_nullable: !!col.is_nullable,
        is_partition: !!col.is_partition,
        is_clustered: !!col.is_clustered,
        is_pii: !!col.is_pii,
        is_audit: !!col.is_audit,
        is_mandatory: !!col.is_mandatory,
      })),
      ports: (contract.ports ?? []).map((p: any) => ({
        object: p.object ?? '',
        properties: (p.properties ?? []).map((prop: any) => ({
          // backend menyimpan `property`; `name` fallback utk data lama
          name: prop.property ?? prop.name ?? '',
          value: prop.value ?? '',
        })),
      })),
    })
  }, [contract, form])

  const { fields: stakeholders, append: addStakeholder, remove: removeStakeholder } = useFieldArray({ control: form.control, name: 'metadata.stakeholders' })
  const { fields: consumers, append: addConsumer, remove: removeConsumer } = useFieldArray({ control: form.control, name: 'metadata.consumer' })
  const { fields: columns, append: addColumn, remove: removeColumn } = useFieldArray({ control: form.control, name: 'model' })
  const { fields: ports, append: addPort, remove: removePort } = useFieldArray({ control: form.control, name: 'ports' })
  const { fields: qualityRules, append: addQuality, remove: removeQuality } = useFieldArray({ control: form.control, name: 'metadata.quality' })


  const [retentionValue, setRetentionValue] = useState('')
  const [retentionUnit, setRetentionUnit] = useState<string>('tahun')

  useEffect(() => {
    setValue('metadata.sla.retention', retentionValue ? `${retentionValue} ${retentionUnit}` : '', { shouldValidate: form.formState.isSubmitted })
  }, [retentionValue, retentionUnit])

  const onSubmit = async (data: FormData) => {
    setIsSubmitting(true)
    try {
      const sla = data.metadata.sla as any
      const slaPayload = {
        availability_start: sla?.availability_start,
        availability_end: sla?.availability_end,
        availability_unit: sla?.availability_unit,
        frequency: sla?.frequency,
        frequency_unit: sla?.frequency_unit,
        ...(sla?.frequency_cron ? { frequency_cron: sla.frequency_cron } : {}),
        ...(retentionValue ? { retention: parseInt(retentionValue, 10), retention_unit: retentionUnit } : {}),
      }
      const payload = {
        ...data,
        metadata: {
          ...data.metadata,
          stakeholders: data.metadata.stakeholders?.filter(s => s.name) ?? [],
          consumer: (data.metadata.consumer ?? []).filter(c => c.name?.trim()),
          quality: data.metadata.quality?.filter(q => q.code) ?? [],
          description: {
            purpose: data.metadata.description?.purpose || undefined,
            usage: data.metadata.description?.usage || undefined,
          },
          sla: slaPayload,
        },
        model: data.model?.filter(c => c.column) ?? [],
        // Backend (PortsProperties) memakai field `property`, bukan `name`.
        ports: (data.ports ?? [])
          .filter(p => p.object)
          .map(p => ({
            object: p.object,
            properties: (p.properties ?? [])
              .filter(pr => pr.name)
              .map(pr => ({ property: pr.name, value: pr.value })),
          })),
        examples: (contract as any)?.examples ?? { type: null, data: null },
      }
      await updateContract(cn, payload)
      // Detail page cache 'contract' bisa stale (mis. tab YAML masih
      // tampilkan data lama). Mark stale TANPA await — kalau refetch
      // throw karena alasan apa pun, jangan ganggu success path.
      queryClient.invalidateQueries({ queryKey: ['contract', cn] })
      toast.success('Data contract berhasil diperbarui!')
      router.push(`/contracts/${cn}`)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Gagal memperbarui kontrak.'
      toast.error(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  const { watch, register, formState: { errors }, setValue } = form

  if (isLoading) {
    return (
      <div className="max-w-3xl space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (!contract) {
    return (
      <div className="text-center py-16 text-muted-foreground">
        <p className="font-medium text-slate-700">Kontrak tidak ditemukan</p>
        <Button variant="outline" className="mt-4" onClick={() => router.back()}>Kembali</Button>
      </div>
    )
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <Button variant="ghost" size="sm" onClick={() => router.back()} className="-ml-2 mb-2 text-muted-foreground">
            <ArrowLeft size={15} className="mr-1" /> Kembali
          </Button>
          <h2 className="text-xl font-semibold text-slate-900">Edit Data Contract</h2>
          <p className="text-sm text-muted-foreground mt-1">
            <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs">{cn}</code>
            {' · '}{contract.metadata?.name}
          </p>
        </div>
        <ImportYamlButton
          context="detail"
          contractNumber={cn}
          userRole={userRole as any}
          onPrefill={(data) => {
            form.reset(data as any)
            toast.success('Form berhasil diperbarui dari YAML')
          }}
        />
      </div>

      {/* Section tabs */}
      <div className="flex gap-1 border-b">
        {SECTIONS.map((s, i) => (
          <button key={i} type="button"
            onClick={() => setActiveSection(i)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeSection === i
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-muted-foreground hover:text-slate-700'
            }`}>
            {s}
          </button>
        ))}
      </div>

      <form
        onSubmit={form.handleSubmit(onSubmit, (errs) => {
          // Jangan biarkan tombol Simpan "diam" saat validasi gagal.
          // Surface error stakeholders spesifik (ADR-0007) ke toast.
          const sErr = (errs as any)?.metadata?.stakeholders
          const sMsg = sErr?.message ?? sErr?.root?.message
          toast.error(sMsg ?? 'Ada field wajib yang belum terisi. Periksa kembali tiap bagian form.')
        })}
        className="space-y-4"
        onKeyDown={(e) => { if (e.key === 'Enter' && (e.target as HTMLElement).tagName !== 'TEXTAREA') e.preventDefault() }}
      >

        {/* ── Informasi Dasar ─────────────────────────────────────── */}
        {activeSection === 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Informasi Dasar</CardTitle>
              <CardDescription>Field dengan tanda * wajib diisi</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Standar Versi *</Label>
                  <Input {...register('standard_version')} />
                  {errors.standard_version && <p className="text-xs text-destructive">{errors.standard_version.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label>Nomor Kontrak</Label>
                  <Input disabled {...register('contract_number')} className="bg-slate-50 text-muted-foreground" />
                  <p className="text-xs text-muted-foreground">Nomor kontrak tidak dapat diubah</p>
                </div>
              </div>
              <Separator />
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Nama Kontrak *</Label>
                  <Input {...register('metadata.name')} />
                  {errors.metadata?.name && <p className="text-xs text-destructive">{errors.metadata.name.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label>Pemilik *</Label>
                  <Controller
                    control={form.control}
                    name="metadata.owner"
                    render={({ field }) => {
                      const inCatalog = !field.value || domainOptions.some(d => d.name === field.value)
                      return (
                        <Select value={field.value || ''} onValueChange={(v) => { if (v) field.onChange(v) }}>
                          <SelectTrigger>
                            <SelectValue placeholder={domainOptions.length === 0 ? 'Belum ada domain di katalog' : 'Pilih domain pemilik'} />
                          </SelectTrigger>
                          <SelectContent>
                            {!inCatalog && (
                              <SelectItem value={field.value as string} className="italic text-muted-foreground">
                                {field.value} (di luar katalog)
                              </SelectItem>
                            )}
                            {domainOptions.map(d => (
                              <SelectItem key={d.name} value={d.name}>{d.label || d.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )
                    }}
                  />
                  {errors.metadata?.owner && <p className="text-xs text-destructive">{errors.metadata.owner.message}</p>}
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <Label>Tipe Kontrak *</Label>
                  {/* Controller: integrasi Select terkontrol dgn RHF — nilai
                      dari form.reset (data kontrak) ter-load benar ke Select. */}
                  <Controller
                    control={form.control}
                    name="metadata.type"
                    render={({ field }) => (
                      // `if (v)`: abaikan onValueChange("") spurious dari
                      // SelectBubbleInput Radix yang menghapus nilai saat load.
                      <Select value={field.value || ''} onValueChange={(v) => { if (v) field.onChange(v) }}>
                        <SelectTrigger><SelectValue placeholder="Pilih tipe" /></SelectTrigger>
                        <SelectContent>
                          {CONTRACT_TYPES.map(t => <SelectItem key={t} value={t} className="capitalize">{t}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    )}
                  />
                  {errors.metadata?.type && <p className="text-xs text-destructive">{errors.metadata.type.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label>Versi *</Label>
                  <Input {...register('metadata.version')} />
                  {errors.metadata?.version && <p className="text-xs text-destructive">{errors.metadata.version.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label>Mode Konsumsi</Label>
                  <Controller
                    control={form.control}
                    name="metadata.consumption_mode"
                    render={({ field }) => (
                      <Select value={field.value || ''} onValueChange={(v) => { if (v) field.onChange(v) }}>
                        <SelectTrigger><SelectValue placeholder="Pilih mode" /></SelectTrigger>
                        <SelectContent>
                          {CONSUMPTION_MODES.map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
              </div>
              <Separator />
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Tanggal Mulai Berlaku *</Label>
                  <Input type="date" {...register('metadata.effective_date')} />
                  {errors.metadata?.effective_date && <p className="text-xs text-destructive">{errors.metadata.effective_date.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label>Tanggal Berakhir *</Label>
                  <Input type="date" {...register('metadata.expiry_date')} />
                  {errors.metadata?.expiry_date && <p className="text-xs text-destructive">{errors.metadata.expiry_date.message}</p>}
                </div>
              </div>
              <Separator />
              <div className="space-y-1.5">
                <Label>Tujuan *</Label>
                <Textarea rows={3} {...register('metadata.description.purpose')} />
                {errors.metadata?.description?.purpose && <p className="text-xs text-destructive">{errors.metadata.description.purpose.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label>Cara Penggunaan *</Label>
                <Textarea rows={3} {...register('metadata.description.usage')} />
                {errors.metadata?.description?.usage && <p className="text-xs text-destructive">{errors.metadata.description.usage.message}</p>}
              </div>
            </CardContent>
          </Card>
        )}

        {/* ── SLA & Stakeholders ──────────────────────────────────── */}
        {activeSection === 1 && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">SLA (Tingkat Layanan)</CardTitle>
                <CardDescription>Ketersediaan, frekuensi, dan retensi data wajib diisi</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <Label>Ketersediaan *</Label>
                  <div className="flex gap-2 items-center flex-wrap">
                    <span className="text-sm text-slate-500 whitespace-nowrap">Jam mulai</span>
                    <Input type="number" min={0} max={23} className="w-20" placeholder="0–23"
                      {...register('metadata.sla.availability_start')} />
                    <span className="text-sm text-slate-500 whitespace-nowrap">Jam selesai</span>
                    <Input type="number" min={0} max={23} className="w-20" placeholder="0–23"
                      {...register('metadata.sla.availability_end')} />
                    <Controller name="metadata.sla.availability_unit" control={form.control}
                      render={({ field }) => (
                        <Select value={field.value} onValueChange={field.onChange}>
                          <SelectTrigger className="w-24"><SelectValue placeholder="Unit" /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="h">Jam</SelectItem>
                            <SelectItem value="d">Hari</SelectItem>
                          </SelectContent>
                        </Select>
                      )} />
                  </div>
                  {errors.metadata?.sla?.availability_start && <p className="text-xs text-destructive">{errors.metadata.sla.availability_start.message}</p>}
                  {errors.metadata?.sla?.availability_end && <p className="text-xs text-destructive">{errors.metadata.sla.availability_end.message}</p>}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label>Frekuensi Update *</Label>
                    <div className="flex gap-2">
                      <Input type="number" min={0} className="w-24" placeholder="Interval"
                        {...register('metadata.sla.frequency')} />
                      <Controller name="metadata.sla.frequency_unit" control={form.control}
                        render={({ field }) => (
                          <Select value={field.value} onValueChange={field.onChange}>
                            <SelectTrigger className="flex-1"><SelectValue placeholder="Unit" /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="m">Menit</SelectItem>
                              <SelectItem value="h">Jam</SelectItem>
                              <SelectItem value="d">Hari</SelectItem>
                            </SelectContent>
                          </Select>
                        )} />
                    </div>
                    {errors.metadata?.sla?.frequency && <p className="text-xs text-destructive">{errors.metadata.sla.frequency.message}</p>}
                  </div>
                  <div className="space-y-1.5">
                    <Label>Retensi Data *</Label>
                    <div className="flex gap-2">
                      <Input type="number" min="1" placeholder="Jumlah" className="w-24"
                        value={retentionValue} onChange={(e) => setRetentionValue(e.target.value)} />
                      <Select value={retentionUnit} onValueChange={setRetentionUnit}>
                        <SelectTrigger className="flex-1"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          {RETENTION_UNITS.map(u => <SelectItem key={u} value={u} className="capitalize">{u}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                    {errors.metadata?.sla?.retention && <p className="text-xs text-destructive">{errors.metadata.sla.retention.message}</p>}
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label>Jadwal Cron <span className="text-slate-400 text-xs">(opsional)</span></Label>
                  <Input placeholder="Contoh: 0 6 * * *" {...register('metadata.sla.frequency_cron')} />
                  {errors.metadata?.sla?.frequency_cron && <p className="text-xs text-destructive">{errors.metadata.sla.frequency_cron.message}</p>}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">Pemangku Kepentingan</CardTitle>
                    <CardDescription>Orang-orang yang terlibat dalam kontrak ini</CardDescription>
                  </div>
                  <Button type="button" variant="outline" size="sm"
                    onClick={() => addStakeholder({ name: '', role: '', email: '', username: undefined, date_in: new Date().toISOString().slice(0, 10), date_out: '' })}>
                    <Plus size={14} className="mr-1" />Tambah
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <p className="text-sm text-amber-800">
                    <strong>Wajib:</strong> minimal 1 pemangku kepentingan dengan peran <strong>Consumer</strong> atau <strong>Producer</strong> agar tim terkait dapat melihat kontrak.
                  </p>
                </div>
                {stakeholders.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">Belum ada pemangku kepentingan.</p>
                )}
                {stakeholders.map((field, i) => {
                  const usernameVal = watch(`metadata.stakeholders.${i}.username`) ?? ''
                  const role = watch(`metadata.stakeholders.${i}.role`) ?? ''
                  const needsUsername = role === 'owner' || role === 'producer' || role === 'consumer'
                  return (
                  <div key={field.id} className="space-y-2 p-3 bg-slate-50 rounded-lg">
                    <div className="grid grid-cols-3 gap-3">
                    <div className="space-y-1">
                      <Label className="text-xs">Nama *</Label>
                      <Input className="h-8 text-xs" {...register(`metadata.stakeholders.${i}.name`)} />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Peran *</Label>
                      <Select
                        value={role}
                        onValueChange={(v) => {
                          setValue(`metadata.stakeholders.${i}.role`, v)
                        }}
                      >
                        <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Pilih peran" /></SelectTrigger>
                        <SelectContent>
                          {STAKEHOLDER_ROLE_GROUPS.map(g => (
                            <SelectGroup key={g.group}>
                              <SelectLabel className="text-xs">{g.group}</SelectLabel>
                              {g.items.map(r => (
                                <SelectItem key={r.value} value={r.value} className="text-xs">{r.label}</SelectItem>
                              ))}
                            </SelectGroup>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Email *</Label>
                      <div className="flex gap-1">
                        <Input className="h-8 text-xs" {...register(`metadata.stakeholders.${i}.email`)} />
                        <Button type="button" variant="ghost" size="icon" className="h-8 w-8 text-red-400 hover:text-red-600 hover:bg-red-50 shrink-0"
                          onClick={() => removeStakeholder(i)}>
                          <Trash2 size={13} />
                        </Button>
                      </div>
                      {errors.metadata?.stakeholders?.[i]?.email && <p className="text-xs text-destructive mt-1">{errors.metadata.stakeholders[i]?.email?.message}</p>}
                    </div>
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs flex items-center gap-1.5">
                        Akun User
                        {needsUsername
                          ? <span className="text-[10px] uppercase font-medium text-amber-600 bg-amber-50 border border-amber-200 px-1 py-0.5 rounded">wajib untuk approver</span>
                          : <span className="text-[10px] text-muted-foreground">opsional</span>}
                      </Label>
                      <Select
                        value={usernameVal || '__none__'}
                        onValueChange={(v) => {
                          const newUsername = v === '__none__' ? undefined : v
                          setValue(`metadata.stakeholders.${i}.username`, newUsername)
                        }}
                      >
                        <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Pilih akun" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="__none__" className="text-xs italic text-muted-foreground">— Tidak terkait akun —</SelectItem>
                          {userOptions.map(u => (
                            <SelectItem key={u.username} value={u.username} className="text-xs">
                              {u.name} <span className="text-muted-foreground">@{u.username}</span>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {needsUsername && !usernameVal && (
                        <p className="text-[11px] text-amber-700">Tanpa akun, stakeholder ini tidak dihitung sebagai approver Owner/Producer/Consumer.</p>
                      )}
                    </div>
                    {/* #114 T1.3 — Tanggal in/out */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <Label className="text-xs">Tanggal Mulai *</Label>
                        <Input type="date" className="h-8 text-xs" {...register(`metadata.stakeholders.${i}.date_in`)} />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs">Tanggal Berakhir <span className="text-muted-foreground font-normal">(opsional)</span></Label>
                        <Input type="date" className="h-8 text-xs" {...register(`metadata.stakeholders.${i}.date_out`)} />
                        {errors.metadata?.stakeholders?.[i]?.date_out && <p className="text-xs text-destructive">{errors.metadata.stakeholders[i]?.date_out?.message}</p>}
                      </div>
                    </div>
                  </div>
                  )
                })}
              </CardContent>
            </Card>

            {/* Konsumen — documentary (ADR-0007): catatan siapa memakai data &
                untuk apa. BUKAN access-control (itu dari stakeholders). */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">Konsumen (Dokumentasi)</CardTitle>
                    <CardDescription>Catatan siapa memakai data ini &amp; untuk apa — opsional, tidak memengaruhi akses kontrak.</CardDescription>
                  </div>
                  <Button type="button" variant="outline" size="sm"
                    onClick={() => addConsumer({ name: '', use_case: '' })}>
                    <Plus size={14} className="mr-1" />Tambah
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {consumers.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">Belum ada konsumen terdokumentasi. Opsional — klik &quot;Tambah&quot; untuk mencatat pemakai data.</p>
                )}
                {consumers.map((field, i) => (
                  <div key={field.id} className="border rounded-lg p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-muted-foreground">Konsumen #{i + 1}</span>
                      <Button type="button" variant="ghost" size="sm" className="h-7 px-2"
                        onClick={() => removeConsumer(i)}>
                        <Trash2 size={13} />
                      </Button>
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Nama Konsumen *</Label>
                      <Input className="h-8 text-xs" placeholder="mis. Tim Analitik"
                        {...register(`metadata.consumer.${i}.name`)} />
                      {errors.metadata?.consumer?.[i]?.name && <p className="text-xs text-destructive">{errors.metadata.consumer[i]?.name?.message}</p>}
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Kegunaan <span className="text-muted-foreground font-normal">(opsional)</span></Label>
                      <Textarea className="text-xs" rows={2} placeholder="mis. menggabungkan dataset dengan data transaksi untuk analisis riwayat pembelian"
                        {...register(`metadata.consumer.${i}.use_case`)} />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        )}

        {/* ── Struktur Data ────────────────────────────────────────── */}
        {activeSection === 2 && (
          <div className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">Struktur Data (Model)</CardTitle>
                  <CardDescription>Definisi kolom dalam data contract</CardDescription>
                </div>
                <Button type="button" variant="outline" size="sm"
                  onClick={() => addColumn({ column: '', business_name: '', logical_type: '', physical_type: '', description: '', is_primary: false, is_nullable: true, is_partition: false, is_clustered: false, is_pii: false, is_audit: false, is_mandatory: false })}>
                  <Plus size={14} className="mr-1" />Tambah Kolom
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {columns.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-6">Belum ada kolom.</p>
              )}
              {columns.map((field, i) => (
                <div key={field.id} className="p-4 border rounded-lg space-y-3 bg-slate-50">
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="font-mono text-xs">Kolom {i + 1}</Badge>
                    <Button type="button" variant="ghost" size="icon" className="h-7 w-7 text-red-400 hover:text-red-600 hover:bg-red-50"
                      onClick={() => removeColumn(i)}>
                      <Trash2 size={13} />
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <Label className="text-xs">Nama Kolom *</Label>
                      <Input placeholder="column_name" className="h-8 text-xs font-mono" {...register(`model.${i}.column`)} />
                      {errors.model?.[i]?.column && <p className="text-xs text-destructive">{errors.model[i]?.column?.message}</p>}
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Nama Bisnis</Label>
                      <Input placeholder="Nama ramah pengguna" className="h-8 text-xs" {...register(`model.${i}.business_name`)} />
                    </div>
                  </div>
                  <TooltipProvider delayDuration={150}>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-1.5">
                          <Label className="text-xs">Tipe Data Bisnis *</Label>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button type="button" aria-label="Penjelasan Tipe Data Bisnis"
                                className="text-slate-400 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-300 rounded">
                                <Info className="h-3.5 w-3.5" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="top" className="max-w-xs">{DATA_TYPE_HELP.logical.tooltip}</TooltipContent>
                          </Tooltip>
                        </div>
                        <Input placeholder="Contoh: Tanggal, Nama, Nilai..." className="h-8 text-xs" {...register(`model.${i}.logical_type`)} />
                        {errors.model?.[i]?.logical_type && <p className="text-[10px] text-destructive">{errors.model[i]?.logical_type?.message}</p>}
                        <p className="text-[10px] text-muted-foreground">{DATA_TYPE_HELP.logical.examples}</p>
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center gap-1.5">
                          <Label className="text-xs">Tipe Data Teknis *</Label>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button type="button" aria-label="Penjelasan Tipe Data Teknis"
                                className="text-slate-400 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-300 rounded">
                                <Info className="h-3.5 w-3.5" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="top" className="max-w-xs">{DATA_TYPE_HELP.physical.tooltip}</TooltipContent>
                          </Tooltip>
                        </div>
                        <Input placeholder="Contoh: VARCHAR(255), INT, DATE..." className="h-8 text-xs font-mono" {...register(`model.${i}.physical_type`)} />
                        {errors.model?.[i]?.physical_type && <p className="text-[10px] text-destructive">{errors.model[i]?.physical_type?.message}</p>}
                        <p className="text-[10px] text-muted-foreground">{DATA_TYPE_HELP.physical.examples}</p>
                      </div>
                    </div>
                  </TooltipProvider>
                  <div className="space-y-1">
                    <Label className="text-xs">Deskripsi *</Label>
                    <Input placeholder="Penjelasan singkat kolom ini" className="h-8 text-xs" {...register(`model.${i}.description`)} />
                    {errors.model?.[i]?.description && <p className="text-[10px] text-destructive">{errors.model[i]?.description?.message}</p>}
                  </div>
                  <TooltipProvider delayDuration={150}>
                    <div className="flex gap-6 flex-wrap">
                      {([
                        { key: 'is_primary', label: 'Primary Key' },
                        { key: 'is_nullable', label: 'Nullable' },
                        { key: 'is_partition', label: 'Partisi' },
                        { key: 'is_clustered', label: 'Cluster' },
                        { key: 'is_pii', label: 'Data PII' },
                        { key: 'is_audit', label: 'Audit' },
                        { key: 'is_mandatory', label: 'Wajib' },
                      ] as const).map(({ key, label }) => (
                        <div key={key} className="flex items-center gap-2">
                          <Checkbox
                            id={`${field.id}-${key}`}
                            checked={!!watch(`model.${i}.${key}`)}
                            onCheckedChange={(v) => setValue(`model.${i}.${key}`, !!v)}
                          />
                          <Label htmlFor={`${field.id}-${key}`} className="text-xs font-normal cursor-pointer">{label}</Label>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                aria-label={`Penjelasan ${label}`}
                                className="text-slate-400 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-300 rounded"
                              >
                                <Info className="h-3.5 w-3.5" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="top">
                              {COLUMN_FLAG_HELP[key]?.description ?? label}
                            </TooltipContent>
                          </Tooltip>
                        </div>
                      ))}
                    </div>
                  </TooltipProvider>
                </div>
              ))}
            </CardContent>
          </Card>

          <QualityRulesEditor
            contractNumber={cn}
            columns={watch('model') ?? []}
            datasetRules={watch('metadata.quality') ?? []}
            columnRules={Object.fromEntries(
              (watch('model') ?? []).map((col: any) => [col.column, col.quality ?? []])
            )}
            onSave={(dsRules, colRulesMap) => {
              setValue('metadata.quality', dsRules)
              const currentModel = form.getValues('model') ?? []
              currentModel.forEach((col, i) => {
                setValue(`model.${i}.quality` as any, colRulesMap[col.column] ?? [])
              })
              toast.success('Aturan kualitas berhasil diperbarui')
            }}
            userMode={isBusinessUser(userRole) ? 'biz' : 'eng'}
            canSwitchMode={userRole === 'admin' || userRole === 'root'}
          />
          </div>
        )}

        {/* ── Koneksi / Port ───────────────────────────────────────── */}
        {activeSection === 3 && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">Koneksi (Port)</CardTitle>
                  <CardDescription>Sumber atau tujuan data contract</CardDescription>
                </div>
                <Button type="button" variant="outline" size="sm"
                  onClick={() => addPort({ object: '', properties: [] })}>
                  <Plus size={14} className="mr-1" />Tambah Port
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {ports.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-6">Belum ada port.</p>
              )}
              {ports.map((portField, i) => (
                <div key={portField.id} className="p-4 border rounded-lg space-y-3 bg-slate-50">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1 flex-1 mr-4">
                      <Label className="text-xs">Nama Objek *</Label>
                      <Input placeholder="Contoh: schema.table_name" className="h-8 text-xs font-mono"
                        {...register(`ports.${i}.object`)} />
                    </div>
                    <Button type="button" variant="ghost" size="icon" className="h-7 w-7 text-red-400 hover:text-red-600 hover:bg-red-50 mt-5"
                      onClick={() => removePort(i)}>
                      <Trash2 size={13} />
                    </Button>
                  </div>
                  <PortProperties portIndex={i} form={form} />
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* ── Action bar ───────────────────────────────────────────── */}
        <div className="flex justify-between pt-2">
          <div className="flex gap-2">
            {activeSection > 0 && (
              <Button type="button" variant="outline" onClick={() => setActiveSection(s => s - 1)}>
                Sebelumnya
              </Button>
            )}
            {activeSection < SECTIONS.length - 1 && (
              <Button type="button" onClick={() => setActiveSection(s => s + 1)}>
                Selanjutnya
              </Button>
            )}
          </div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save size={15} className="mr-2" />}
            {isSubmitting ? 'Menyimpan...' : 'Simpan Perubahan'}
          </Button>
        </div>
      </form>
    </div>
  )
}

function PortProperties({ portIndex, form }: { portIndex: number; form: any }) {
  // properties (nested array) dikelola via watch+setValue — useFieldArray
  // dengan nama dinamis dilarang (crash saat index parent bergeser, CLAUDE.md).
  const props: { name?: string; value?: string }[] = form.watch(`ports.${portIndex}.properties`) ?? []
  const setProps = (next: typeof props) => form.setValue(`ports.${portIndex}.properties`, next)
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label className="text-xs text-muted-foreground">Properties</Label>
        <Button type="button" variant="ghost" size="sm" className="h-6 text-xs"
          onClick={() => setProps([...props, { name: '', value: '' }])}>
          <Plus size={11} className="mr-1" />Tambah
        </Button>
      </div>
      {props.map((_, j) => (
        <div key={j} className="flex gap-2">
          <Input placeholder="nama" className="h-7 text-xs" {...form.register(`ports.${portIndex}.properties.${j}.name`)} />
          <Input placeholder="nilai" className="h-7 text-xs" {...form.register(`ports.${portIndex}.properties.${j}.value`)} />
          <Button type="button" variant="ghost" size="icon" className="h-7 w-7 text-red-400 shrink-0"
            onClick={() => setProps(props.filter((_, k) => k !== j))}>
            <Trash2 size={11} />
          </Button>
        </div>
      ))}
    </div>
  )
}
