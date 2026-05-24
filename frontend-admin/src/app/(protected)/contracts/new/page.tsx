'use client'

import { useState, useEffect } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { addContract, generateContractNumber, getUsersBasic } from '@/lib/api/admin'
import { getMe } from '@/lib/api/auth'
import { useQuery } from '@tanstack/react-query'
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
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { toast } from 'sonner'
import { Plus, Trash2, Loader2, RefreshCw, ChevronRight, ChevronLeft, Check, Info } from 'lucide-react'
import { cn } from '@/lib/utils'
import { CONTRACT_TYPES, CONSUMPTION_MODES, STAKEHOLDER_ROLE_GROUPS, RETENTION_UNITS, QUALITY_DIMENSIONS } from '@/types/contract'
import { COLUMN_FLAG_HELP, DATA_TYPE_HELP } from '@/lib/field-help'

// ─── Schema ───────────────────────────────────────────────────────────────────
const schema = z.object({
  standard_version: z.string().min(1, 'Wajib diisi'),
  contract_number: z.string().min(1, 'Wajib diisi'),
  metadata: z.object({
    version: z.string().min(1, 'Wajib diisi'),
    type: z.string().min(1, 'Pilih tipe kontrak'),
    name: z.string().min(1, 'Wajib diisi'),
    owner: z.string().min(1, 'Wajib diisi'),
    consumption_mode: z.string().optional(),
    description: z.object({
      purpose: z.string().optional(),
      usage: z.string().optional(),
    }).optional(),
    sla: z.object({
      availability: z.string().optional(),
      frequency: z.string().optional(),
      retention: z.string().optional(),
      cron: z.string().optional(),
    }).optional(),
    stakeholders: z.array(z.object({
      name: z.string().min(1, 'Nama wajib diisi'),
      role: z.string().min(1, 'Peran wajib diisi'),
      email: z.string().optional(),
      // ADR-0004: link ke dgrusr.username — wajib bila stakeholder ini
      // ingin menjadi approver Producer/Consumer.
      username: z.string().optional(),
    })).optional(),
    quality: z.array(z.object({
      code: z.string().min(1, 'Kode wajib diisi'),
      dimension: z.string().optional(),
      description: z.string().optional(),
      impact: z.string().optional(),
      severity: z.string().optional(),
      custom_properties: z.array(z.object({
        property: z.string(),
        value: z.string(),
      })).optional(),
    })).optional(),
  }),
  model: z.array(z.object({
    column: z.string().min(1, 'Nama kolom wajib diisi'),
    business_name: z.string().optional(),
    logical_type: z.string().optional(),
    physical_type: z.string().optional(),
    description: z.string().optional(),
    is_primary: z.boolean().optional(),
    is_nullable: z.boolean().optional(),
    is_pii: z.boolean().optional(),
    is_mandatory: z.boolean().optional(),
    quality: z.array(z.object({
      code: z.string().min(1),
      dimension: z.string().optional(),
      description: z.string().optional(),
      impact: z.string().optional(),
      severity: z.string().optional(),
      custom_properties: z.array(z.object({
        property: z.string(),
        value: z.string(),
      })).optional(),
    })).optional(),
  })).optional(),
  // Koneksi opsional — field lenient supaya port/properti kosong tidak
  // memblokir submit; baris kosong dibuang di onSubmit.
  ports: z.array(z.object({
    object: z.string().optional(),
    properties: z.array(z.object({
      name: z.string().optional(),
      value: z.string().optional(),
    })).optional(),
  })).optional(),
})

type FormData = z.infer<typeof schema>

// ─── Step indicator ───────────────────────────────────────────────────────────
const STEPS = ['Informasi Dasar', 'SLA', 'Pemangku', 'Struktur Data', 'Koneksi', 'Tinjauan']

function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex items-center gap-0 mb-8">
      {STEPS.map((label, i) => (
        <div key={i} className="flex items-center flex-1 last:flex-none">
          <div className="flex flex-col items-center gap-1">
            <div className={cn(
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors',
              i < current ? 'bg-emerald-500 text-white' :
              i === current ? 'bg-indigo-600 text-white' :
              'bg-slate-100 text-slate-400'
            )}>
              {i < current ? <Check size={14} /> : i + 1}
            </div>
            <span className={cn('text-xs whitespace-nowrap hidden sm:block', i === current ? 'text-slate-900 font-medium' : 'text-slate-400')}>
              {label}
            </span>
          </div>
          {i < STEPS.length - 1 && (
            <div className={cn('flex-1 h-px mx-2', i < current ? 'bg-emerald-400' : 'bg-slate-200')} />
          )}
        </div>
      ))}
    </div>
  )
}

// ─── Review (Tinjauan) ────────────────────────────────────────────────────────
function ReviewRow({ label, value }: { label: string; value?: React.ReactNode }) {
  const empty = value === undefined || value === null || value === '' ||
    (Array.isArray(value) && value.length === 0)
  return (
    <div className="flex gap-3">
      <span className="text-sm text-muted-foreground w-40 shrink-0">{label}</span>
      <span className="text-sm font-medium">
        {empty ? <span className="text-muted-foreground italic font-normal">—</span> : value}
      </span>
    </div>
  )
}

function ReviewSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 border-b pb-1">{title}</h4>
      <div className="space-y-1 pt-0.5">{children}</div>
    </div>
  )
}

// Render seluruh isi kontrak — dipakai di step Tinjauan agar maintainer
// melihat data utuh sebelum menyimpan.
function ContractReview({ data, retentionValue, retentionUnit }: {
  data: FormData
  retentionValue: string
  retentionUnit: string
}) {
  const stakeholders = data.metadata?.stakeholders ?? []
  const model = data.model ?? []
  const ports = data.ports ?? []
  const dsQuality = data.metadata?.quality ?? []

  return (
    <div className="space-y-5">
      <ReviewSection title="Informasi Dasar">
        <ReviewRow label="Nama Kontrak" value={data.metadata?.name} />
        <ReviewRow label="Pemilik" value={data.metadata?.owner} />
        <ReviewRow label="Nomor Kontrak" value={data.contract_number} />
        <ReviewRow label="Tipe" value={data.metadata?.type} />
        <ReviewRow label="Versi" value={data.metadata?.version} />
        <ReviewRow label="Standar" value={data.standard_version} />
        <ReviewRow label="Mode Konsumsi" value={data.metadata?.consumption_mode} />
        <ReviewRow label="Tujuan" value={data.metadata?.description?.purpose} />
        <ReviewRow label="Cara Penggunaan" value={data.metadata?.description?.usage} />
      </ReviewSection>

      <ReviewSection title="SLA">
        <ReviewRow label="Ketersediaan" value={data.metadata?.sla?.availability} />
        <ReviewRow label="Frekuensi Update" value={data.metadata?.sla?.frequency} />
        <ReviewRow label="Retensi Data" value={retentionValue ? `${retentionValue} ${retentionUnit}` : ''} />
        <ReviewRow label="Jadwal Cron" value={data.metadata?.sla?.cron} />
      </ReviewSection>

      <ReviewSection title={`Pemangku Kepentingan (${stakeholders.length})`}>
        {stakeholders.length === 0 ? (
          <p className="text-sm text-muted-foreground italic">Belum ada pemangku kepentingan.</p>
        ) : stakeholders.map((s, i) => (
          <div key={i} className="text-sm">
            <span className="font-medium">{s.name || '—'}</span>
            {s.role && <span className="text-muted-foreground"> · {s.role}</span>}
            {s.email && <span className="text-muted-foreground"> · {s.email}</span>}
            {s.username && <span className="text-indigo-600"> · @{s.username}</span>}
          </div>
        ))}
      </ReviewSection>

      <ReviewSection title={`Struktur Data — Kolom (${model.length})`}>
        {model.length === 0 ? (
          <p className="text-sm text-muted-foreground italic">Belum ada kolom.</p>
        ) : model.map((c, i) => {
          const flags = [
            c.is_primary && 'PK', c.is_nullable && 'nullable',
            c.is_pii && 'PII', c.is_mandatory && 'wajib',
          ].filter(Boolean) as string[]
          const qn = (c.quality ?? []).length
          return (
            <div key={i} className="text-sm">
              <span className="font-medium font-mono">{c.column || '—'}</span>
              {(c.logical_type || c.physical_type) && (
                <span className="text-muted-foreground"> · {[c.logical_type, c.physical_type].filter(Boolean).join(' / ')}</span>
              )}
              {flags.length > 0 && <span className="text-muted-foreground"> · {flags.join(', ')}</span>}
              {qn > 0 && <span className="text-muted-foreground"> · {qn} aturan kualitas</span>}
            </div>
          )
        })}
      </ReviewSection>

      {dsQuality.length > 0 && (
        <ReviewSection title={`Aturan Kualitas Dataset (${dsQuality.length})`}>
          {dsQuality.map((q, i) => (
            <div key={i} className="text-sm">
              <span className="font-medium">{q.code}</span>
              {q.dimension && <span className="text-muted-foreground"> · {q.dimension}</span>}
            </div>
          ))}
        </ReviewSection>
      )}

      <ReviewSection title={`Koneksi (${ports.length})`}>
        {ports.length === 0 ? (
          <p className="text-sm text-muted-foreground italic">Tidak ada koneksi.</p>
        ) : ports.map((p, i) => {
          const props = (p.properties ?? []).filter(pr => pr.name)
          return (
            <div key={i} className="text-sm">
              <span className="font-medium font-mono">{p.object || '—'}</span>
              {props.length > 0 && (
                <span className="text-muted-foreground"> · {props.map(pr => `${pr.name}=${pr.value}`).join(', ')}</span>
              )}
            </div>
          )
        })}
      </ReviewSection>
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function NewContractPage() {
  const router = useRouter()
  const [step, setStep] = useState(0)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isGenCN, setIsGenCN] = useState(false)
  const { data: user } = useQuery({ queryKey: ['me'], queryFn: getMe })
  const userRole = user?.group_access ?? 'user'
  // Direktori user untuk dropdown stakeholder (ADR-0004).
  const { data: userOptions = [] } = useQuery({ queryKey: ['users-basic'], queryFn: getUsersBasic })

  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      standard_version: '1.0',
      contract_number: '',
      metadata: {
        version: '1.0.0',
        type: '',
        name: '',
        owner: '',
        consumption_mode: '',
        description: { purpose: '', usage: '' },
        sla: { availability: '', frequency: '', retention: '', cron: '' },
        stakeholders: [],
        quality: [],
      },
      model: [],
      ports: [],
    },
  })

  const { watch, register, formState: { errors }, setValue } = form

  const { fields: stakeholders, append: addStakeholder, remove: removeStakeholder } = useFieldArray({ control: form.control, name: 'metadata.stakeholders' })
  const { fields: columns, append: addColumn, remove: removeColumn } = useFieldArray({ control: form.control, name: 'model' })
  const { fields: ports, append: addPort, remove: removePort } = useFieldArray({ control: form.control, name: 'ports' })

  const [retentionValue, setRetentionValue] = useState('')
  const [retentionUnit, setRetentionUnit] = useState<string>('tahun')

  useEffect(() => {
    setValue('metadata.sla.retention', retentionValue ? `${retentionValue} ${retentionUnit}` : '')
  }, [retentionValue, retentionUnit])

  const generateCN = async () => {
    setIsGenCN(true)
    try {
      const cn = await generateContractNumber()
      form.setValue('contract_number', cn)
    } catch { toast.error('Gagal generate nomor kontrak') }
    finally { setIsGenCN(false) }
  }

  useEffect(() => { generateCN() }, [])

  const nextStep = async () => {
    // Index = step. Hanya step 0 (Informasi Dasar) punya field wajib;
    // SLA/Pemangku/Struktur Data/Koneksi semuanya opsional.
    const fieldsPerStep: (keyof FormData | string)[][] = [
      ['standard_version', 'contract_number', 'metadata.version', 'metadata.type', 'metadata.name', 'metadata.owner'],
      [], [], [], [],
    ]
    const valid = await form.trigger((fieldsPerStep[step] ?? []) as any)
    if (valid) setStep(s => Math.min(s + 1, STEPS.length - 1))
  }

  const onSubmit = async (data: FormData) => {
    // Safety net: form hanya boleh disubmit dari step terakhir (Tinjauan).
    // Root cause sudah diperbaiki di tombol navigasi (key + preventDefault),
    // guard ini tetap dipertahankan sebagai lapisan terakhir.
    if (step !== STEPS.length - 1) return
    setIsSubmitting(true)
    try {
      // Clean empty optional values
      // Build SLA — retention must be sent as int + unit separately
      const slaBase = Object.fromEntries(
        Object.entries(data.metadata.sla ?? {})
          .filter(([k, v]) => v && k !== 'retention')
      )
      const slaPayload = {
        ...slaBase,
        ...(retentionValue
          ? { retention: parseInt(retentionValue, 10), retention_unit: retentionUnit }
          : {}),
      }

      const payload = {
        ...data,
        metadata: {
          ...data.metadata,
          stakeholders: data.metadata.stakeholders?.filter(s => s.name) ?? [],
          quality: (data.metadata.quality ?? [])
            .filter(q => q.code)
            .map(q => ({ ...q, custom_properties: (q.custom_properties ?? []).filter(p => p.property) })),
          description: {
            purpose: data.metadata.description?.purpose || undefined,
            usage: data.metadata.description?.usage || undefined,
          },
          sla: slaPayload,
        },
        model: (data.model ?? [])
          .filter(c => c.column)
          .map(c => ({
            ...c,
            quality: ((c as any).quality ?? [])
              .filter((q: any) => q.code)
              .map((q: any) => ({ ...q, custom_properties: (q.custom_properties ?? []).filter((p: any) => p.property) })),
          })),
        // Backend (PortsProperties) memakai field `property`, bukan `name`.
        ports: (data.ports ?? [])
          .filter(p => p.object)
          .map(p => ({
            object: p.object,
            properties: (p.properties ?? [])
              .filter(pr => pr.name)
              .map(pr => ({ property: pr.name, value: pr.value })),
          })),
        examples: { type: null, data: null },
      }
      await addContract(payload)
      const cn = watch('contract_number')
      toast.success('Data contract berhasil disimpan!')
      router.push(cn ? `/contracts/${cn}` : '/contracts')
    } catch (err: unknown) {
      const detail = (err as any)?.response?.data?.detail
      let msg = 'Gagal menyimpan kontrak.'
      if (typeof detail === 'string') msg = detail
      else if (Array.isArray(detail)) msg = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
      toast.error(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Tambah Data Contract</h2>
          <p className="text-sm text-muted-foreground mt-1">Isi formulir berikut untuk mendaftarkan kontrak data baru</p>
        </div>
        <ImportYamlButton
          context="new"
          userRole={userRole as any}
          onPrefill={(data) => {
            form.reset(data as any)
            toast.success('Form berhasil diisi dari YAML')
          }}
        />
      </div>

      <StepIndicator current={step} />

      <form
        onSubmit={form.handleSubmit(onSubmit)}
        onKeyDown={(e) => { if (e.key === 'Enter' && (e.target as HTMLElement).tagName !== 'TEXTAREA') e.preventDefault() }}
      >

        {/* ── Step 0: Informasi Dasar ─────────────────────────────── */}
        {step === 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Informasi Dasar</CardTitle>
              <CardDescription>Field dengan tanda * wajib diisi</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Standar Versi *</Label>
                  <Input placeholder="1.0" {...register('standard_version')} />
                  {errors.standard_version && <p className="text-xs text-destructive">{errors.standard_version.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label>Nomor Kontrak *</Label>
                  <div className="flex gap-2">
                    <Input placeholder="Auto-generate" {...register('contract_number')} />
                    <Button type="button" variant="outline" size="icon" onClick={generateCN} disabled={isGenCN} title="Generate ulang">
                      <RefreshCw size={14} className={isGenCN ? 'animate-spin' : ''} />
                    </Button>
                  </div>
                  {errors.contract_number && <p className="text-xs text-destructive">{errors.contract_number.message}</p>}
                </div>
              </div>

              <Separator />

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Nama Kontrak *</Label>
                  <Input placeholder="Contoh: Data Penjualan Harian" {...register('metadata.name')} />
                  {errors.metadata?.name && <p className="text-xs text-destructive">{errors.metadata.name.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label>Pemilik *</Label>
                  <Input placeholder="Contoh: Tim Penjualan" {...register('metadata.owner')} />
                  {errors.metadata?.owner && <p className="text-xs text-destructive">{errors.metadata.owner.message}</p>}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <Label>Tipe Kontrak *</Label>
                  <Select onValueChange={(v) => setValue('metadata.type', v)} defaultValue="">
                    <SelectTrigger><SelectValue placeholder="Pilih tipe" /></SelectTrigger>
                    <SelectContent>
                      {CONTRACT_TYPES.map(t => <SelectItem key={t} value={t} className="capitalize">{t}</SelectItem>)}
                    </SelectContent>
                  </Select>
                  {errors.metadata?.type && <p className="text-xs text-destructive">{errors.metadata.type.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label>Versi *</Label>
                  <Input placeholder="1.0.0" {...register('metadata.version')} />
                  {errors.metadata?.version && <p className="text-xs text-destructive">{errors.metadata.version.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label>Mode Konsumsi</Label>
                  <Select onValueChange={(v) => setValue('metadata.consumption_mode', v)} defaultValue="">
                    <SelectTrigger><SelectValue placeholder="Pilih mode" /></SelectTrigger>
                    <SelectContent>
                      {CONSUMPTION_MODES.map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Separator />

              <div className="space-y-1.5">
                <Label>Tujuan</Label>
                <Textarea placeholder="Jelaskan tujuan penggunaan data contract ini..." rows={3}
                  {...register('metadata.description.purpose')} />
              </div>
              <div className="space-y-1.5">
                <Label>Cara Penggunaan</Label>
                <Textarea placeholder="Bagaimana cara menggunakan data ini?" rows={3}
                  {...register('metadata.description.usage')} />
              </div>
            </CardContent>
          </Card>
        )}

        {/* ── Step 1: SLA ──────────────────────────────────────────── */}
        {step === 1 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">SLA (Tingkat Layanan)</CardTitle>
                <CardDescription>Semua field opsional</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Ketersediaan</Label>
                  <Input placeholder="Contoh: 99.9%" {...register('metadata.sla.availability')} />
                </div>
                <div className="space-y-1.5">
                  <Label>Frekuensi Update</Label>
                  <Input placeholder="Contoh: Harian, Jam 06.00" {...register('metadata.sla.frequency')} />
                </div>
                <div className="space-y-1.5">
                  <Label>Retensi Data</Label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      min="1"
                      placeholder="Jumlah"
                      className="w-24"
                      value={retentionValue}
                      onChange={(e) => setRetentionValue(e.target.value)}
                    />
                    <Select value={retentionUnit} onValueChange={setRetentionUnit}>
                      <SelectTrigger className="flex-1"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {RETENTION_UNITS.map(u => <SelectItem key={u} value={u} className="capitalize">{u}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label>Jadwal Cron</Label>
                  <Input placeholder="Contoh: 0 6 * * *" {...register('metadata.sla.cron')} />
                </div>
              </CardContent>
            </Card>
        )}

        {/* ── Step 2: Pemangku Kepentingan ─────────────────────────── */}
        {step === 2 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">Pemangku Kepentingan</CardTitle>
                    <CardDescription>Orang-orang yang terlibat dalam kontrak ini</CardDescription>
                  </div>
                  <Button type="button" variant="outline" size="sm"
                    onClick={() => addStakeholder({ name: '', role: '', email: '', username: undefined })}>
                    <Plus size={14} className="mr-1" />Tambah
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {stakeholders.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">Belum ada pemangku kepentingan. Klik &quot;Tambah&quot; untuk menambah.</p>
                )}
                {stakeholders.map((field, i) => {
                  const usernameVal = watch(`metadata.stakeholders.${i}.username`) ?? ''
                  const role = watch(`metadata.stakeholders.${i}.role`) ?? ''
                  const needsUsername = role === 'owner' || role === 'producer' || role === 'consumer'
                  return (
                  <div key={field.id} className="space-y-2 p-3 bg-slate-50 rounded-lg relative">
                    <div className="grid grid-cols-3 gap-3">
                    <div className="space-y-1">
                      <Label className="text-xs">Nama *</Label>
                      <Input placeholder="Nama lengkap" className="h-8 text-xs" {...register(`metadata.stakeholders.${i}.name`)} />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Peran *</Label>
                      <Select
                        value={role}
                        onValueChange={(v) => setValue(`metadata.stakeholders.${i}.role`, v)}
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
                      <Label className="text-xs">Email</Label>
                      <div className="flex gap-1">
                        <Input placeholder="email@domain.com" className="h-8 text-xs" {...register(`metadata.stakeholders.${i}.email`)} />
                        <Button type="button" variant="ghost" size="icon" className="h-8 w-8 text-red-400 hover:text-red-600 hover:bg-red-50 shrink-0"
                          onClick={() => removeStakeholder(i)}>
                          <Trash2 size={13} />
                        </Button>
                      </div>
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
                        onValueChange={(v) => setValue(
                          `metadata.stakeholders.${i}.username`,
                          v === '__none__' ? undefined : v,
                        )}
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
                  </div>
                  )
                })}
              </CardContent>
            </Card>
        )}

        {/* ── Step 3: Model / Struktur Data ────────────────────────── */}
        {step === 3 && (
          <div className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">Struktur Data (Model)</CardTitle>
                  <CardDescription>Definisikan kolom-kolom dalam data contract ini</CardDescription>
                </div>
                <Button type="button" variant="outline" size="sm"
                  onClick={() => addColumn({ column: '', business_name: '', logical_type: '', physical_type: '', description: '', is_primary: false, is_nullable: true, is_pii: false, is_mandatory: false, quality: [] })}>
                  <Plus size={14} className="mr-1" />Tambah Kolom
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {columns.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-6">Belum ada kolom. Klik &quot;Tambah Kolom&quot; untuk menambah.</p>
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
                          <Label className="text-xs">Tipe Data Bisnis</Label>
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
                        <p className="text-[10px] text-muted-foreground">{DATA_TYPE_HELP.logical.examples}</p>
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center gap-1.5">
                          <Label className="text-xs">Tipe Data Teknis</Label>
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
                        <p className="text-[10px] text-muted-foreground">{DATA_TYPE_HELP.physical.examples}</p>
                      </div>
                    </div>
                  </TooltipProvider>
                  <div className="space-y-1">
                    <Label className="text-xs">Deskripsi</Label>
                    <Input placeholder="Penjelasan singkat kolom ini" className="h-8 text-xs" {...register(`model.${i}.description`)} />
                  </div>
                  <TooltipProvider delayDuration={150}>
                    <div className="flex gap-6 flex-wrap">
                      {([
                        { key: 'is_primary', label: 'Primary Key' },
                        { key: 'is_nullable', label: 'Nullable' },
                        { key: 'is_pii', label: 'Data PII' },
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
            contractNumber={watch('contract_number')}
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
            userMode={userRole === 'user' ? 'biz' : 'eng'}
            canSwitchMode={userRole === 'admin' || userRole === 'root'}
          />
          </div>
        )}

        {/* ── Step 4: Koneksi (Port) ───────────────────────────────── */}
        {step === 4 && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">Koneksi (Port)</CardTitle>
                  <CardDescription>Sumber atau tujuan data contract — opsional</CardDescription>
                </div>
                <Button type="button" variant="outline" size="sm"
                  onClick={() => addPort({ object: '', properties: [] })}>
                  <Plus size={14} className="mr-1" />Tambah Port
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {ports.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-6">
                  Belum ada koneksi. Opsional — klik &quot;Tambah Port&quot; bila kontrak punya sumber/tujuan data.
                </p>
              )}
              {ports.map((portField, i) => {
                // properties (nested array) dikelola via watch+setValue —
                // useFieldArray dengan nama dinamis dilarang (lihat CLAUDE.md).
                const props = watch(`ports.${i}.properties`) ?? []
                return (
                  <div key={portField.id} className="p-4 border rounded-lg space-y-3 bg-slate-50">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1 flex-1 mr-4">
                        <Label className="text-xs">Nama Objek *</Label>
                        <Input placeholder="Contoh: schema.table_name" className="h-8 text-xs font-mono"
                          {...register(`ports.${i}.object`)} />
                      </div>
                      <Button type="button" variant="ghost" size="icon"
                        className="h-7 w-7 text-red-400 hover:text-red-600 hover:bg-red-50 mt-5"
                        onClick={() => removePort(i)}>
                        <Trash2 size={13} />
                      </Button>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-xs text-muted-foreground">Properties</Label>
                        <Button type="button" variant="ghost" size="sm" className="h-6 text-xs"
                          onClick={() => setValue(`ports.${i}.properties`, [...props, { name: '', value: '' }])}>
                          <Plus size={11} className="mr-1" />Tambah
                        </Button>
                      </div>
                      {props.length === 0 && (
                        <p className="text-[11px] text-muted-foreground">Belum ada properti.</p>
                      )}
                      {props.map((_, j) => (
                        <div key={j} className="flex gap-2">
                          <Input placeholder="nama" className="h-7 text-xs"
                            {...register(`ports.${i}.properties.${j}.name`)} />
                          <Input placeholder="nilai" className="h-7 text-xs"
                            {...register(`ports.${i}.properties.${j}.value`)} />
                          <Button type="button" variant="ghost" size="icon" className="h-7 w-7 text-red-400 shrink-0"
                            onClick={() => setValue(`ports.${i}.properties`, props.filter((_, k) => k !== j))}>
                            <Trash2 size={11} />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </CardContent>
          </Card>
        )}

        {/* ── Step 5: Review ───────────────────────────────────────── */}
        {step === 5 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Tinjauan Sebelum Simpan</CardTitle>
              <CardDescription>Periksa seluruh isi kontrak di bawah sebelum menyimpan</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <ContractReview data={watch()} retentionValue={retentionValue} retentionUnit={retentionUnit} />
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-sm text-amber-800">
                  Pastikan semua informasi sudah benar sebelum menyimpan. Kontrak yang sudah disimpan tidak dapat diedit melalui antarmuka ini.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* ── Navigation ───────────────────────────────────────────── */}
        <div className="flex justify-between mt-6">
          <Button type="button" variant="outline" onClick={() => step === 0 ? router.back() : setStep(s => s - 1)}>
            <ChevronLeft size={16} className="mr-1" />
            {step === 0 ? 'Batal' : 'Sebelumnya'}
          </Button>

          {/* key wajib berbeda: tanpa key React pakai ulang DOM node tombol
              yang sama untuk kedua cabang ternary. nextStep async → setStep
              resolve di microtask SELAMA event klik, menambal atribut type
              dari button ke submit sebelum browser proses default action →
              form ter-submit. key terpisah memaksa DOM node berbeda;
              preventDefault menetralkan default action bila timing lolos. */}
          {step < STEPS.length - 1 ? (
            <Button key="nav-next" type="button" onClick={(e) => { e.preventDefault(); nextStep() }}>
              Selanjutnya <ChevronRight size={16} className="ml-1" />
            </Button>
          ) : (
            <Button key="nav-submit" type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isSubmitting ? 'Menyimpan...' : 'Simpan Kontrak'}
            </Button>
          )}
        </div>
      </form>
    </div>
  )
}

