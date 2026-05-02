'use client'

/**
 * Halaman: /catalog/new
 * Form untuk menambah modul aturan baru ke katalog (model patching).
 * Hanya root dan admin.
 */

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createRule } from '@/lib/api/catalog'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Separator } from '@/components/ui/separator'
import { toast } from 'sonner'
import { ArrowLeft, Plus, Trash2, Loader2 } from 'lucide-react'
import { DIMENSION_LABELS } from '@/types/rule_catalog'

// ─── Schema ───────────────────────────────────────────────────────────────────

const paramSchema = z.object({
  key:       z.string().min(1, 'Key wajib diisi').regex(/^[a-z_]+$/, 'Hanya huruf kecil dan underscore'),
  label:     z.string().min(1, 'Label wajib diisi'),
  type:      z.enum(['text', 'number', 'select', 'multi', 'date']),
  required:  z.boolean(),
  hint:      z.string().optional(),
  min_value: z.coerce.number().optional(),
  max_value: z.coerce.number().optional(),
  options:   z.array(z.object({ value: z.string().min(1), label: z.string().min(1) })).optional(),
})

const schema = z.object({
  code:              z.string().min(1, 'Wajib diisi').regex(/^[a-z_]+$/, 'Hanya huruf kecil dan underscore (snake_case)'),
  label:             z.string().min(1, 'Wajib diisi'),
  description:       z.string().optional(),
  layer:             z.enum(['dataset', 'column', 'both']),
  dimension:         z.enum(['completeness', 'validity', 'accuracy', 'security']),
  sentence_template: z.string().min(1, 'Wajib diisi').includes('{', { message: 'Template harus mengandung {placeholder}' }),
  params:            z.array(paramSchema),
})

type FormValues = z.infer<typeof schema>

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function NewCatalogPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [previewSentence, setPreviewSentence] = useState('')

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      code: '',
      label: '',
      description: '',
      layer: 'column',
      dimension: 'completeness',
      sentence_template: 'Pastikan {column} ',
      params: [],
    },
  })

  const { fields: params, append: appendParam, remove: removeParam } = useFieldArray({
    control: form.control,
    name: 'params',
  })

  const createMutation = useMutation({
    mutationFn: createRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rule-catalog'] })
      toast.success('Modul berhasil ditambahkan ke katalog.')
      router.push('/catalog')
    },
    onError: (err: unknown) => {
      const detail = (err as any)?.response?.data?.detail
      let msg = 'Gagal menyimpan modul.'
      if (typeof detail === 'string') msg = detail
      else if (Array.isArray(detail)) msg = detail.map((e: { msg?: string }) => e.msg ?? JSON.stringify(e)).join('; ')
      toast.error(msg)
    },
  })

  const onSubmit = (values: FormValues) => {
    createMutation.mutate(values)
  }

  // Live sentence preview
  const updatePreview = () => {
    const tpl = form.getValues('sentence_template')
    const params = form.getValues('params')
    let preview = tpl
    params.forEach(p => {
      preview = preview.replaceAll(`{${p.key}}`, p.label ? `[${p.label}]` : `[${p.key}]`)
    })
    setPreviewSentence(preview)
  }

  return (
    <div className="max-w-3xl space-y-5">
      {/* Header */}
      <div>
        <Button variant="ghost" size="sm" className="mb-2 -ml-2 text-zinc-500" onClick={() => router.back()}>
          <ArrowLeft size={14} className="mr-1" /> Kembali
        </Button>
        <h2 className="text-xl font-semibold text-zinc-900">Tambah Modul Aturan Baru</h2>
        <p className="text-sm text-zinc-500 mt-1">
          Definisikan jenis aturan kustom. Modul baru langsung tersedia di semua form aturan kualitas.
        </p>
      </div>

      <div className="rounded-md border border-purple-200 bg-purple-50 px-3 py-2.5 text-xs text-purple-800 flex gap-2">
        <span>⬡</span>
        Modul baru akan muncul di Sentence Builder tanpa perlu perubahan kode.
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        {/* Identitas */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Identitas Modul</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label className="text-xs">Nama untuk User Bisnis *</Label>
                <Input {...form.register('label')} placeholder="contoh: Tidak Boleh Kosong" className="h-9 text-sm" />
                {form.formState.errors.label && (
                  <p className="text-xs text-red-500">{form.formState.errors.label.message}</p>
                )}
                <p className="text-[11px] text-zinc-400">Ditampilkan di sentence builder</p>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Kode Teknis * <span className="font-mono text-[10px] text-zinc-400">(snake_case)</span></Label>
                <Input {...form.register('code')} placeholder="null_check" className="h-9 text-sm font-mono" />
                {form.formState.errors.code && (
                  <p className="text-xs text-red-500">{form.formState.errors.code.message}</p>
                )}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">Deskripsi Singkat</Label>
              <Input {...form.register('description')} placeholder="Jelaskan kegunaan aturan ini..." className="h-9 text-sm" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label className="text-xs">Berlaku di Layer *</Label>
                <Select
                  value={form.watch('layer')}
                  onValueChange={v => form.setValue('layer', v as FormValues['layer'])}
                >
                  <SelectTrigger className="h-9 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="column">Kolom (column)</SelectItem>
                    <SelectItem value="dataset">Dataset (dataset)</SelectItem>
                    <SelectItem value="both">Keduanya (both)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Dimensi Kualitas *</Label>
                <Select
                  value={form.watch('dimension')}
                  onValueChange={v => form.setValue('dimension', v as FormValues['dimension'])}
                >
                  <SelectTrigger className="h-9 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(DIMENSION_LABELS).map(([v, l]) => (
                      <SelectItem key={v} value={v}>{l} ({v})</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">Template Kalimat *</Label>
              <Input
                {...form.register('sentence_template', { onChange: updatePreview })}
                placeholder="Pastikan kolom {column} tidak boleh kosong"
                className="h-9 text-sm"
              />
              {form.formState.errors.sentence_template && (
                <p className="text-xs text-red-500">{form.formState.errors.sentence_template.message}</p>
              )}
              <p className="text-[11px] text-zinc-400">
                Gunakan <code className="bg-zinc-100 px-1 rounded">{'{nama_param}'}</code> sebagai placeholder. Contoh: <code className="bg-zinc-100 px-1 rounded">{'Pastikan {column} panjangnya {length} karakter'}</code>
              </p>
              {previewSentence && (
                <div className="mt-1.5 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                  <span className="font-semibold">Preview: </span>{previewSentence}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Parameters */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm">Schema Parameter</CardTitle>
                <CardDescription className="text-xs mt-0.5">
                  Parameter ini menentukan input apa yang muncul di sentence builder saat aturan ini dipilih.
                </CardDescription>
              </div>
              <Button
                type="button"
                size="sm"
                className="bg-amber-500 hover:bg-amber-600 text-white gap-1.5 h-8"
                onClick={() => {
                  appendParam({ key: '', label: '', type: 'text', required: true })
                  updatePreview()
                }}
              >
                <Plus size={12} /> Tambah Parameter
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {params.length === 0 ? (
              <p className="text-xs text-zinc-400 text-center py-4 border border-dashed border-zinc-200 rounded-lg">
                Belum ada parameter. Klik "Tambah Parameter" untuk mulai.
              </p>
            ) : (
              <div className="space-y-4">
                {params.map((field, i) => (
                  <div key={field.id} className="rounded-lg border border-zinc-200 p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-zinc-500">Parameter {i + 1}</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-zinc-400 hover:text-red-500"
                        onClick={() => { removeParam(i); updatePreview() }}
                      >
                        <Trash2 size={12} />
                      </Button>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1.5">
                        <Label className="text-xs">Key <span className="text-zinc-400 font-mono text-[10px]">(harus cocok dengan {'{placeholder}'})</span></Label>
                        <Input
                          {...form.register(`params.${i}.key`, { onChange: updatePreview })}
                          placeholder="length"
                          className="h-8 text-xs font-mono"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label className="text-xs">Label Bisnis</Label>
                        <Input
                          {...form.register(`params.${i}.label`, { onChange: updatePreview })}
                          placeholder="Panjang karakter"
                          className="h-8 text-xs"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-3 items-center">
                      <div className="space-y-1.5">
                        <Label className="text-xs">Tipe Input</Label>
                        <Select
                          value={form.watch(`params.${i}.type`)}
                          onValueChange={v => form.setValue(`params.${i}.type`, v as FormValues['params'][0]['type'])}
                        >
                          <SelectTrigger className="h-8 text-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="text">Teks bebas</SelectItem>
                            <SelectItem value="number">Angka</SelectItem>
                            <SelectItem value="select">Pilihan (dropdown)</SelectItem>
                            <SelectItem value="multi">Multi-pilih</SelectItem>
                            <SelectItem value="date">Tanggal</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      {form.watch(`params.${i}.type`) === 'number' && (
                        <>
                          <div className="space-y-1.5">
                            <Label className="text-xs">Nilai minimum</Label>
                            <Input type="number" {...form.register(`params.${i}.min_value`)} className="h-8 text-xs" placeholder="1" />
                          </div>
                          <div className="space-y-1.5">
                            <Label className="text-xs">Nilai maksimum</Label>
                            <Input type="number" {...form.register(`params.${i}.max_value`)} className="h-8 text-xs" placeholder="255" />
                          </div>
                        </>
                      )}
                      <div className="flex items-center gap-2 mt-5">
                        <Checkbox
                          id={`req-${i}`}
                          checked={form.watch(`params.${i}.required`)}
                          onCheckedChange={v => form.setValue(`params.${i}.required`, !!v)}
                        />
                        <Label htmlFor={`req-${i}`} className="text-xs cursor-pointer">Wajib diisi</Label>
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs">Teks bantuan (opsional)</Label>
                      <Input {...form.register(`params.${i}.hint`)} placeholder="Antara 1 – 255 karakter" className="h-8 text-xs" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => router.back()}>Batal</Button>
          <Button
            type="submit"
            className="bg-amber-500 hover:bg-amber-600 text-white gap-1.5"
            disabled={createMutation.isPending}
          >
            {createMutation.isPending && <Loader2 size={13} className="animate-spin" />}
            Simpan Modul
          </Button>
        </div>
      </form>
    </div>
  )
}
