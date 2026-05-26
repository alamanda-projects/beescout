'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import {
  getDomains,
  createDomain,
  updateDomain,
  deactivateDomain,
  type DomainRecord,
} from '@/lib/api/admin'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { Loader2, Boxes, Plus, Info, Pencil, Save, X, ShieldOff, ShieldCheck } from 'lucide-react'

// ─── Helpers ────────────────────────────────────────────────────────────────
function apiError(err: unknown, fallback: string): string {
  const detail = (err as any)?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
  return fallback
}

// Pratinjau slug — harus cocok dengan slugify_domain() di backend.
function slugPreview(raw: string): string {
  return raw.trim().toLowerCase().split(/\s+/).filter(Boolean).join('-')
}

// ─── Schema ─────────────────────────────────────────────────────────────────
const createSchema = z.object({
  name: z.string().min(1, 'Nama domain wajib diisi').max(60),
  label: z.string().min(1, 'Label wajib diisi').max(80),
  description: z.string().max(200).optional(),
})
type CreateFormData = z.infer<typeof createSchema>

const editSchema = z.object({
  label: z.string().min(1, 'Label wajib diisi').max(80),
  description: z.string().max(200).optional(),
})
type EditFormData = z.infer<typeof editSchema>

// ─── Edit row ───────────────────────────────────────────────────────────────
function EditPanel({ domain, onClose, onSaved }: {
  domain: DomainRecord
  onClose: () => void
  onSaved: () => void
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: { label: domain.label, description: domain.description ?? '' },
  })

  const { mutate, isPending } = useMutation({
    mutationFn: (data: EditFormData) =>
      updateDomain(domain.name, { label: data.label, description: data.description ?? '' }),
    onSuccess: () => { toast.success(`Domain "${domain.name}" diperbarui.`); onSaved() },
    onError: (err) => toast.error(apiError(err, 'Gagal memperbarui domain.')),
  })

  return (
    <tr>
      <td colSpan={6} className="p-0">
        <div className="bg-indigo-50 border-y border-indigo-100 px-4 py-4">
          <form onSubmit={handleSubmit((d) => mutate(d))} className="space-y-3">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-semibold text-indigo-700">
                Edit Domain: <span className="font-mono">{domain.name}</span>
              </p>
              <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-600">
                <X size={15} />
              </button>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <Label className="text-xs">Label (nama tampil) *</Label>
                <Input className="h-8 text-xs" {...register('label')} />
                {errors.label && <p className="text-[10px] text-destructive">{errors.label.message}</p>}
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Deskripsi</Label>
                <Input className="h-8 text-xs" {...register('description')} />
              </div>
            </div>
            <p className="text-[10px] text-muted-foreground">
              Slug <span className="font-mono">{domain.name}</span> tidak bisa diubah — itu kunci akses kontrak.
            </p>
            <div className="flex justify-end gap-2 pt-1">
              <Button type="button" variant="outline" size="sm" onClick={onClose}>Batal</Button>
              <Button type="submit" size="sm" disabled={isPending}>
                {isPending ? <Loader2 size={13} className="animate-spin mr-1" /> : <Save size={13} className="mr-1" />}
                Simpan
              </Button>
            </div>
          </form>
        </div>
      </td>
    </tr>
  )
}

// ─── Page ───────────────────────────────────────────────────────────────────
export default function DomainsPage() {
  const queryClient = useQueryClient()
  const [editTarget, setEditTarget] = useState<string | null>(null)

  const { data: domains = [], isLoading } = useQuery({
    queryKey: ['domains', 'all'],
    queryFn: () => getDomains(true),
  })

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<CreateFormData>({
    resolver: zodResolver(createSchema),
    defaultValues: { name: '', label: '', description: '' },
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['domains'] })

  const { mutate: create, isPending: creating } = useMutation({
    mutationFn: (data: CreateFormData) =>
      createDomain({ name: data.name, label: data.label, description: data.description }),
    onSuccess: (res: any) => {
      toast.success(res?.message ?? 'Domain berhasil dibuat.')
      reset()
      invalidate()
    },
    onError: (err) => toast.error(apiError(err, 'Gagal membuat domain.')),
  })

  const { mutate: toggleActive } = useMutation({
    mutationFn: ({ name, is_active }: { name: string; is_active: boolean }) =>
      is_active ? updateDomain(name, { is_active: true }) : deactivateDomain(name),
    onSuccess: (_, vars) => {
      toast.success(`Domain "${vars.name}" ${vars.is_active ? 'diaktifkan' : 'dinonaktifkan'}.`)
      invalidate()
    },
    onError: (err) => toast.error(apiError(err, 'Gagal mengubah status domain.')),
  })

  const namePreview = slugPreview(watch('name') ?? '')
  const activeCount = domains.filter(d => d.is_active).length

  return (
    <div className="space-y-5 max-w-4xl">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Domain Data</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Daftar domain terstandarisasi untuk assignment user. Domain dipakai sebagai
          kunci akses kontrak — gunakan katalog ini agar tidak ada typo / inkonsistensi.
        </p>
      </div>

      <div className="flex items-center gap-2 text-xs text-indigo-700 bg-indigo-50 border border-indigo-100 rounded-lg px-3 py-2">
        <Info size={13} className="shrink-0" />
        Domain tidak dihapus permanen — hanya dinonaktifkan, karena user lama mungkin masih memakainya.
      </div>

      {/* Form tambah */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Plus size={16} /> Tambah Domain
          </CardTitle>
          <CardDescription>
            Nama akan diubah otomatis menjadi slug huruf kecil (kunci matching).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((d) => create(d))} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Nama Domain *</Label>
                <Input placeholder="Contoh: Penjualan" {...register('name')} />
                {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
                {namePreview && (
                  <p className="text-xs text-muted-foreground">
                    Slug: <code className="bg-slate-100 px-1 rounded font-mono">{namePreview}</code>
                  </p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label>Label (nama tampil) *</Label>
                <Input placeholder="Contoh: Tim Penjualan B2B" {...register('label')} />
                {errors.label && <p className="text-xs text-destructive">{errors.label.message}</p>}
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Deskripsi <span className="text-muted-foreground">(opsional)</span></Label>
              <Input placeholder="Penjelasan singkat domain ini" {...register('description')} />
              {errors.description && <p className="text-xs text-destructive">{errors.description.message}</p>}
            </div>
            <Button type="submit" disabled={creating}>
              {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
              {creating ? 'Menyimpan...' : 'Tambah Domain'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Tabel */}
      <div className="flex items-center gap-3 text-sm text-muted-foreground">
        <Boxes size={15} />
        <span>{domains.length} domain · {activeCount} aktif</span>
      </div>

      <Card>
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead>Label</TableHead>
              <TableHead className="w-[160px]">Slug</TableHead>
              <TableHead>Deskripsi</TableHead>
              <TableHead className="w-[80px] text-center">User</TableHead>
              <TableHead className="w-[90px] text-center">Status</TableHead>
              <TableHead className="w-[100px] text-center">Aksi</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 6 }).map((_, j) => (
                    <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                  ))}
                </TableRow>
              ))
            ) : domains.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-10 text-muted-foreground text-sm">
                  Belum ada domain. Tambahkan domain pertama melalui form di atas.
                </TableCell>
              </TableRow>
            ) : (
              domains.flatMap((d) => {
                const rows = [
                  <TableRow key={d.name} className={!d.is_active ? 'opacity-50' : ''}>
                    <TableCell className="text-sm font-medium">{d.label}</TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">{d.name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{d.description || '—'}</TableCell>
                    <TableCell className="text-center text-sm">{d.user_count ?? 0}</TableCell>
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        {d.is_active ? (
                          <span className="inline-flex items-center gap-1 text-xs text-emerald-600">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />Aktif
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs text-slate-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />Nonaktif
                          </span>
                        )}
                        {d.is_default && (
                          <span
                            title="Domain bawaan sistem — tidak bisa dinonaktifkan"
                            className="inline-flex items-center rounded border border-amber-200 bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700"
                          >
                            Default
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center justify-center gap-1">
                        <button
                          type="button"
                          title={d.is_default
                            ? 'Domain default tidak bisa dinonaktifkan'
                            : (d.is_active ? 'Nonaktifkan' : 'Aktifkan')}
                          onClick={() => toggleActive({ name: d.name, is_active: !d.is_active })}
                          disabled={d.is_default}
                          className="p-1.5 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-slate-400"
                        >
                          {d.is_active ? <ShieldOff size={14} /> : <ShieldCheck size={14} />}
                        </button>
                        <button
                          type="button"
                          title={d.is_default ? 'Domain default tidak bisa diedit' : 'Edit'}
                          onClick={() => setEditTarget(editTarget === d.name ? null : d.name)}
                          disabled={d.is_default}
                          className={`p-1.5 rounded hover:bg-slate-100 transition-colors disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-slate-400 ${editTarget === d.name ? 'text-indigo-600 bg-indigo-50' : 'text-slate-400 hover:text-slate-700'}`}
                        >
                          <Pencil size={14} />
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>,
                ]
                if (editTarget === d.name) {
                  rows.push(
                    <EditPanel
                      key={`edit-${d.name}`}
                      domain={d}
                      onClose={() => setEditTarget(null)}
                      onSaved={() => { setEditTarget(null); invalidate() }}
                    />,
                  )
                }
                return rows
              })
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
