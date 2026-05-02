'use client'

/**
 * Halaman: /catalog
 * Katalog Aturan Kualitas — hanya root dan admin.
 * Menampilkan semua modul, filter built-in vs kustom,
 * dan tombol tambah modul baru.
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAllRules, deleteRule } from '@/lib/api/catalog'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import Link from 'next/link'
import { Plus, Search, Trash2, Pencil, Lock } from 'lucide-react'
import { cn } from '@/lib/utils'
import { DIMENSION_LABELS, LAYER_LABELS, type RuleCatalogItem } from '@/types/rule_catalog'

// ─── Dimension badge colours ──────────────────────────────────────────────────
const DIM_BADGE: Record<string, string> = {
  completeness: 'bg-green-50 text-green-700 border-green-200',
  validity:     'bg-blue-50 text-blue-700 border-blue-200',
  accuracy:     'bg-amber-50 text-amber-700 border-amber-200',
  security:     'bg-red-50 text-red-700 border-red-200',
}

const LAYER_BADGE: Record<string, string> = {
  dataset: 'bg-blue-50 text-blue-700 border-blue-200',
  column:  'bg-amber-50 text-amber-700 border-amber-200',
  both:    'bg-purple-50 text-purple-700 border-purple-200',
}

// ─── Module card ──────────────────────────────────────────────────────────────
function ModuleCard({
  module,
  onDelete,
}: { module: RuleCatalogItem; onDelete: (code: string) => void }) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-zinc-200 bg-white p-4 hover:border-amber-200 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="flex gap-1.5 flex-wrap">
          <span className={cn('badge inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-semibold', LAYER_BADGE[module.layer])}>
            {LAYER_LABELS[module.layer]}
          </span>
          <span className={cn('inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-semibold', DIM_BADGE[module.dimension])}>
            {DIMENSION_LABELS[module.dimension]}
          </span>
          {module.is_builtin && (
            <span className="inline-flex items-center gap-0.5 rounded border border-zinc-200 bg-zinc-50 px-1.5 py-0.5 text-[10px] font-semibold text-zinc-500">
              <Lock size={8} /> bawaan
            </span>
          )}
          {!module.is_builtin && (
            <span className="inline-flex items-center rounded border border-purple-200 bg-purple-50 px-1.5 py-0.5 text-[10px] font-semibold text-purple-700">
              kustom
            </span>
          )}
        </div>
        {/* Actions — only for custom modules */}
        {!module.is_builtin && (
          <div className="flex gap-1 shrink-0">
            <Button variant="ghost" size="icon" className="h-7 w-7" asChild>
              <Link href={`/catalog/${module.code}/edit`}><Pencil size={12} /></Link>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-zinc-400 hover:text-red-500 hover:bg-red-50"
              onClick={() => onDelete(module.code)}
            >
              <Trash2 size={12} />
            </Button>
          </div>
        )}
      </div>

      <div>
        <div className="font-semibold text-sm text-zinc-900 mb-0.5">{module.label}</div>
        <code className="text-[11px] font-mono text-zinc-400">{module.code}</code>
      </div>

      {module.description && (
        <p className="text-xs text-zinc-500 leading-relaxed">{module.description}</p>
      )}

      <div className="flex items-center justify-between text-xs text-zinc-400 pt-1 border-t border-zinc-100">
        <span>{module.params.length} parameter</span>
        <span className={cn('font-medium', module.is_active ? 'text-green-600' : 'text-zinc-400')}>
          {module.is_active ? 'Aktif' : 'Nonaktif'}
        </span>
      </div>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function CatalogPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'builtin' | 'custom'>('all')

  const { data: rules = [], isLoading } = useQuery({
    queryKey: ['rule-catalog'],
    queryFn: getAllRules,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteRule,
    onSuccess: (_, code) => {
      queryClient.invalidateQueries({ queryKey: ['rule-catalog'] })
      toast.success(`Modul '${code}' berhasil dihapus.`)
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(msg ?? 'Gagal menghapus modul.')
    },
  })

  const handleDelete = (code: string) => {
    if (!confirm(`Hapus modul '${code}'? Tindakan ini tidak bisa dibatalkan.`)) return
    deleteMutation.mutate(code)
  }

  const filtered = rules.filter(r => {
    const matchSearch = !search.trim()
      || r.code.toLowerCase().includes(search.toLowerCase())
      || r.label.toLowerCase().includes(search.toLowerCase())
    const matchFilter =
      filter === 'all' ? true :
      filter === 'builtin' ? r.is_builtin :
      !r.is_builtin
    return matchSearch && matchFilter
  })

  const stats = {
    total:   rules.length,
    builtin: rules.filter(r => r.is_builtin).length,
    custom:  rules.filter(r => !r.is_builtin).length,
    used:    rules.reduce((sum) => sum + 1, 0), // placeholder
  }

  return (
    <div className="space-y-5 max-w-5xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-xl font-semibold text-zinc-900">Katalog Aturan Kualitas</h2>
          <p className="text-sm text-zinc-500 mt-1">
            Kelola modul aturan yang tersedia untuk semua kontrak. Modul bawaan tidak bisa dihapus.
          </p>
        </div>
        <Button asChild className="bg-amber-500 hover:bg-amber-600 text-white gap-1.5">
          <Link href="/catalog/new"><Plus size={14} />Tambah Modul Baru</Link>
        </Button>
      </div>

      {/* Info banner */}
      <div className="rounded-md border border-purple-200 bg-purple-50 px-3 py-2.5 text-xs text-purple-800 flex gap-2">
        <span className="shrink-0 mt-0.5">⬡</span>
        <span>
          <strong>Sistem Modular</strong> — Setiap aturan adalah modul mandiri dengan schema parameter.
          Tambah modul baru kapan saja tanpa mempengaruhi aturan yang sudah ada di kontrak.
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        {[
          [String(stats.total), 'Total Modul', false],
          [String(stats.builtin), 'Modul Bawaan', false],
          [String(stats.custom), 'Modul Kustom', true],
        ].map(([n, l, acc]) => (
          <div
            key={String(l)}
            className={cn(
              'rounded-lg border bg-white p-4',
              acc ? 'border-amber-300 border-t-2 border-t-amber-400' : 'border-zinc-200',
            )}
          >
            <div className={cn('text-2xl font-bold leading-none', acc ? 'text-amber-500' : 'text-zinc-900')}>
              {String(n)}
            </div>
            <div className="text-xs text-zinc-500 mt-1.5">{String(l)}</div>
          </div>
        ))}
      </div>

      {/* Filter + search */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex gap-1">
          {([['all', 'Semua'], ['builtin', 'Bawaan'], ['custom', 'Kustom']] as const).map(([v, l]) => (
            <Button
              key={v}
              variant={filter === v ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter(v)}
              className={cn(filter === v && 'bg-amber-500 hover:bg-amber-600 text-white border-amber-500')}
            >
              {l}
            </Button>
          ))}
        </div>
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
          <Input
            placeholder="Cari kode atau nama modul..."
            className="pl-8 h-9 text-sm"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-3 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full rounded-lg" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-16 text-center text-zinc-400">
          <p className="text-sm font-medium">Tidak ada modul ditemukan</p>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-3">
          {filtered.map(m => (
            <ModuleCard key={m.code} module={m} onDelete={handleDelete} />
          ))}
          {/* Add new tile */}
          <Link
            href="/catalog/new"
            className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-zinc-200 p-8 text-zinc-400 hover:border-amber-300 hover:text-amber-500 transition-colors min-h-[140px]"
          >
            <Plus size={22} />
            <span className="text-xs font-medium">Tambah Modul Baru</span>
          </Link>
        </div>
      )}
    </div>
  )
}
