'use client'

import { useState, useEffect } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { addContract, generateContractNumber } from '@/lib/api/contracts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { toast } from 'sonner'
import { Plus, Trash2, Loader2, ArrowLeft, RefreshCw } from 'lucide-react'

const CONTRACT_TYPES = ['dataset', 'api', 'stream', 'report', 'model'] as const

const schema = z.object({
  contract_number: z.string().min(1, 'Wajib diisi'),
  standard_version: z.string().default('0.0.0'),
  metadata: z.object({
    name: z.string().min(1, 'Wajib diisi'),
    version: z.string().min(1, 'Wajib diisi').default('1.0.0'),
    type: z.string().min(1, 'Pilih tipe kontrak'),
    owner: z.string().min(1, 'Wajib diisi'),
    description: z.object({
      purpose: z.string().optional(),
    }).optional(),
  }),
  model: z.array(z.object({
    column: z.string().min(1, 'Nama kolom wajib diisi'),
    logical_type: z.string().optional(),
    physical_type: z.string().optional(),
    description: z.string().optional(),
  })).optional(),
})

type FormValues = z.infer<typeof schema>

function FieldError({ msg }: { msg?: string }) {
  if (!msg) return null
  return <p className="text-xs text-red-500 mt-1">{msg}</p>
}

export default function NewContractPage() {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [loadingCn, setLoadingCn] = useState(false)

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      contract_number: '',
      standard_version: '0.0.0',
      metadata: { name: '', version: '1.0.0', type: '', owner: '', description: { purpose: '' } },
      model: [],
    },
  })

  const { fields: modelFields, append: appendModel, remove: removeModel } = useFieldArray({
    control: form.control,
    name: 'model',
  })

  async function loadContractNumber() {
    setLoadingCn(true)
    try {
      const cn = await generateContractNumber()
      form.setValue('contract_number', cn)
    } catch {
      toast.error('Gagal generate nomor kontrak.')
    } finally {
      setLoadingCn(false)
    }
  }

  useEffect(() => { loadContractNumber() }, [])

  async function onSubmit(values: FormValues) {
    setIsSubmitting(true)
    try {
      await addContract({
        ...values,
        ports: [],
        examples: {},
      })
      toast.success('Kontrak berhasil dibuat.')
      router.push('/contracts')
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      let msg = 'Gagal menyimpan kontrak.'
      if (typeof detail === 'string') msg = detail
      else if (Array.isArray(detail)) msg = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
      toast.error(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  const { register, formState: { errors } } = form

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <Button variant="ghost" size="sm" onClick={() => router.back()} className="-ml-2 mb-2 text-muted-foreground">
          <ArrowLeft size={15} className="mr-1" /> Kembali
        </Button>
        <h2 className="text-xl font-semibold text-slate-900">Tambah Kontrak Baru</h2>
        <p className="text-sm text-muted-foreground mt-1">Isi informasi dasar kontrak data Anda</p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
        {/* Nomor Kontrak */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Nomor Kontrak</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Input {...register('contract_number')} placeholder="DCN-..." className="font-mono text-sm" />
              <Button type="button" variant="outline" size="sm" onClick={loadContractNumber} disabled={loadingCn}>
                {loadingCn ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              </Button>
            </div>
            <FieldError msg={errors.contract_number?.message} />
          </CardContent>
        </Card>

        {/* Metadata */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Metadata</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label className="text-xs">Nama Kontrak *</Label>
                <Input {...register('metadata.name')} placeholder="Nama kontrak data" className="text-sm" />
                <FieldError msg={errors.metadata?.name?.message} />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Versi *</Label>
                <Input {...register('metadata.version')} placeholder="1.0.0" className="text-sm" />
                <FieldError msg={errors.metadata?.version?.message} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label className="text-xs">Tipe Kontrak *</Label>
                <select
                  {...register('metadata.type')}
                  className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">Pilih tipe...</option>
                  {CONTRACT_TYPES.map((t) => (
                    <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                  ))}
                </select>
                <FieldError msg={errors.metadata?.type?.message} />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Pemilik *</Label>
                <Input {...register('metadata.owner')} placeholder="Nama tim atau divisi" className="text-sm" />
                <FieldError msg={errors.metadata?.owner?.message} />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">Tujuan (opsional)</Label>
              <textarea
                {...register('metadata.description.purpose')}
                placeholder="Jelaskan tujuan kontrak ini..."
                rows={3}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-none"
              />
            </div>
          </CardContent>
        </Card>

        {/* Model / Kolom */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Kolom Data</CardTitle>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => appendModel({ column: '', logical_type: '', physical_type: '', description: '' })}
              >
                <Plus size={13} className="mr-1" /> Tambah Kolom
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {modelFields.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-4">
                Belum ada kolom. Klik "Tambah Kolom" untuk mulai mendefinisikan skema data.
              </p>
            ) : (
              modelFields.map((field, i) => (
                <div key={field.id} className="rounded-lg border p-3 space-y-3 bg-slate-50">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-600">Kolom #{i + 1}</span>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      className="h-7 w-7 p-0 text-red-400 hover:text-red-600 hover:bg-red-50"
                      onClick={() => removeModel(i)}
                    >
                      <Trash2 size={13} />
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <Label className="text-xs">Nama Kolom *</Label>
                      <Input
                        {...register(`model.${i}.column`)}
                        placeholder="nama_kolom"
                        className="text-sm h-8"
                      />
                      <FieldError msg={errors.model?.[i]?.column?.message} />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Tipe Bisnis</Label>
                      <Input
                        {...register(`model.${i}.logical_type`)}
                        placeholder="UUID, String, Integer..."
                        className="text-sm h-8"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Tipe Teknis</Label>
                      <Input
                        {...register(`model.${i}.physical_type`)}
                        placeholder="VARCHAR(36), INT..."
                        className="text-sm h-8"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Deskripsi</Label>
                      <Input
                        {...register(`model.${i}.description`)}
                        placeholder="Keterangan kolom..."
                        className="text-sm h-8"
                      />
                    </div>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Separator />

        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => router.back()}>
            Batal
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting && <Loader2 size={14} className="mr-1 animate-spin" />}
            Simpan Kontrak
          </Button>
        </div>
      </form>
    </div>
  )
}
