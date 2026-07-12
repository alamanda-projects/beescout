'use client'

/**
 * Halaman: /catalog/{code}/edit
 * Form untuk mengedit modul aturan kustom.
 * Modul bawaan (is_builtin) tidak bisa diedit — backend juga mem-block dengan 403.
 */

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getRuleByCode, updateRule } from '@/lib/api/catalog'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
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

// Edit form: `code` tidak boleh diubah, jadi tidak ikut dalam schema input.
const schema = z.object({
  label:             z.string().min(1, 'Wajib diisi'),
  description:       z.string().optional(),
  layer:             z.enum(['dataset', 'column', 'both']),
  dimension:         z.enum(['completeness', 'validity', 'accuracy', 'security', 'uniqueness', 'timeliness', 'consistency']),
  sentence_template: z.string().min(1, 'Wajib diisi').includes('{', { message: 'Template harus mengandung {placeholder}' }),
  params:            z.array(paramSchema),
})

type FormValues = z.infer<typeof schema>

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function EditCatalogPage() {
  const router = useRouter()
  const params = useParams<{ code: string }>()
  const code = params.code
  const queryClient = useQueryClient()
  const [previewSentence, setPreviewSentence] = useState('')

  const { data: rule, isLoading, error } = useQuery({
    queryKey: ['rule-catalog', code],
    queryFn:  () => getRuleByCode(code),
    enabled:  !!code,
  })

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      label: '',
      description: '',
      layer: 'column',
      dimension: 'completeness',
      sentence_template: '',
      params: [],
    },
  })

  const { fields: paramFields, append: appendParam, remove: removeParam, replace: replaceParams } = useFieldArray({
    control: form.control,
    name: 'params',
  })

  // Prefill setelah data datang. Modul bawaan dilindungi: tendang balik ke list.
  useEffect(() => {
    if (!rule) return
    if (rule.is_builtin) {
      toast.error('Modul bawaan tidak bisa diedit.')
      router.replace('/catalog')
      return
    }
    form.reset({
      label:             rule.label,
      description:       rule.description ?? '',
      layer:             rule.layer,
      dimension:         rule.dimension,
      sentence_template: rule.sentence_template,
      params:            rule.params ?? [],
    })
    replaceParams(rule.params ?? [])
    // Render preview awal pakai data yang baru di-reset.
    const tpl = rule.sentence_template
    let preview = tpl
    ;(rule.params ?? []).forEach(p => {
      preview = preview.replaceAll(`{${p.key}}`, p.label ? `[${p.label}]` : `[${p.key}]`)
    })
    setPreviewSentence(preview)
  }, [rule, form, router, replaceParams])

  const updateMutation = useMutation({
    mutationFn: (values: FormValues) => updateRule(code, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rule-catalog'] })
      queryClient.invalidateQueries({ queryKey: ['rule-catalog', code] })
      toast.success('Modul berhasil diperbarui.')
      router.push('/catalog')
    },
    onError: (err: unknown) => {
      const detail = (err as any)?.response?.data?.detail
      let msg = 'Gagal memperbarui modul.'
      if (typeof detail === 'string') msg = detail
      else if (Array.isArray(detail)) msg = detail.map((e: { msg?: string }) => e.msg ?? JSON.stringify(e)).join('; ')
      toast.error(msg)
    },
  })

  const onSubmit = (values: FormValues) => {
    updateMutation.mutate(values)
  }

  // Live sentence preview
  const updatePreview = () => {
    const tpl = form.getValues('sentence_template')
    const ps = form.getValues('params')
    let preview = tpl
    ps.forEach(p => {
      preview = preview.replaceAll(`{${p.key}}`, p.label ? `[${p.label}]` : `[${p.key}]`)
    })
    setPreviewSentence(preview)
  }

  if (isLoading) {
    return (
      <div className="max-w-3xl flex items-center gap-2 text-sm text-zinc-500 py-10">
        <Loader2 size={14} className="animate-spin" /> Memuat modul...
      </div>
    )
  }

  if (error || !rule) {
    return (
      <div className="max-w-3xl space-y-3">
        <Button variant="ghost" size="sm" className="-ml-2 text-zinc-500" onClick={() => router.push('/catalog')}>
          <ArrowLeft size={14} className="mr-1" /> Kembali ke katalog
        </Button>
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-800">
          Modul <code className="font-mono">{code}</code> tidak ditemukan atau gagal dimuat.
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl space-y-5">
      {/* Header */}
      <div>
        <Button type="button" variant="ghost" size="sm" className="mb-2 -ml-2 text-zinc-500" onClick={() => router.back()}>
          <ArrowLeft size={14} className="mr-1" /> Kembali
        </Button>
        <h2 className="text-xl font-semibold text-zinc-900">Edit Modul Aturan</h2>
        <p className="text-sm text-zinc-500 mt-1">
          Perbarui definisi modul kustom. Kode teknis <code className="font-mono text-xs bg-zinc-100 px-1 rounded">{rule.code}</code> tidak bisa diubah.
        </p>
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
                <Label className="text-xs">Kode Teknis <span className="font-mono text-[10px] text-zinc-400">(tidak bisa diubah)</span></Label>
                <Input value={rule.code} disabled className="h-9 text-sm font-mono bg-zinc-50" />
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
                Gunakan <code className="bg-zinc-100 px-1 rounded">{'{nama_param}'}</code> sebagai placeholder.
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
                  Parameter menentukan input apa yang muncul di sentence builder saat aturan ini dipilih.
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
            {paramFields.length === 0 ? (
              <p className="text-xs text-zinc-400 text-center py-4 border border-dashed border-zinc-200 rounded-lg">
                Belum ada parameter. Klik "Tambah Parameter" untuk mulai.
              </p>
            ) : (
              <div className="space-y-4">
                {paramFields.map((field, i) => (
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
            disabled={updateMutation.isPending}
          >
            {updateMutation.isPending && <Loader2 size={13} className="animate-spin" />}
            Simpan Perubahan
          </Button>
        </div>
      </form>
    </div>
  )
}
