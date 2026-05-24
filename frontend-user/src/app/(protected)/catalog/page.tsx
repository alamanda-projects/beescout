'use client'

/**
 * Halaman: /catalog (user panel)
 * Katalog Aturan Kualitas — read-only untuk developer & user.
 * Lihat issue #26: pengajuan modul baru menyusul setelah #27 (approval workflow).
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getAllRules } from '@/lib/api/catalog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Search, Lock } from 'lucide-react'
import { cn } from '@/lib/utils'
import { DIMENSION_LABELS, LAYER_LABELS, type RuleCatalogItem } from '@/types/rule_catalog'

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

function ModuleCard({ module }: { module: RuleCatalogItem }) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-zinc-200 bg-white p-4 hover:border-indigo-200 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="flex gap-1.5 flex-wrap">
          <span className={cn('inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-semibold', LAYER_BADGE[module.layer])}>
            {LAYER_LABELS[module.layer]}
          </span>
          <span className={cn('inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-semibold', DIM_BADGE[module.dimension])}>
            {DIMENSION_LABELS[module.dimension]}
          </span>
          {module.is_builtin ? (
            <span className="inline-flex items-center gap-0.5 rounded border border-zinc-200 bg-zinc-50 px-1.5 py-0.5 text-[10px] font-semibold text-zinc-500">
              <Lock size={8} /> bawaan
            </span>
          ) : (
            <span className="inline-flex items-center rounded border border-purple-200 bg-purple-50 px-1.5 py-0.5 text-[10px] font-semibold text-purple-700">
              kustom
            </span>
          )}
        </div>
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

export default function CatalogPage() {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'builtin' | 'custom'>('all')

  const { data: rules = [], isLoading } = useQuery({
    queryKey: ['rule-catalog'],
    queryFn: getAllRules,
  })

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
  }

  return (
    <div className="space-y-5 max-w-5xl">
      <div>
        <h2 className="text-xl font-semibold text-zinc-900">Katalog Aturan Kualitas</h2>
        <p className="text-sm text-zinc-500 mt-1">
          Modul aturan yang tersedia untuk dipakai di kontrak. Mode tampilan saja — pengajuan modul baru menyusul.
        </p>
      </div>

      <div className="rounded-md border border-indigo-200 bg-indigo-50 px-3 py-2.5 text-xs text-indigo-800 flex gap-2">
        <span className="shrink-0 mt-0.5">⬡</span>
        <span>
          <strong>Sistem Modular</strong> — Pilih modul dari daftar ini saat menyusun aturan kualitas di kontrak data.
          Hubungi steward jika membutuhkan modul baru.
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          [String(stats.total), 'Total Modul'],
          [String(stats.builtin), 'Modul Bawaan'],
          [String(stats.custom), 'Modul Kustom'],
        ].map(([n, l]) => (
          <div key={l} className="rounded-lg border border-zinc-200 bg-white p-4">
            <div className="text-2xl font-bold leading-none text-zinc-900">{n}</div>
            <div className="text-xs text-zinc-500 mt-1.5">{l}</div>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex gap-1">
          {([['all', 'Semua'], ['builtin', 'Bawaan'], ['custom', 'Kustom']] as const).map(([v, l]) => (
            <Button
              key={v}
              type="button"
              variant={filter === v ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter(v)}
              className={cn(filter === v && 'bg-indigo-600 hover:bg-indigo-700 text-white border-indigo-600')}
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
            <ModuleCard key={m.code} module={m} />
          ))}
        </div>
      )}
    </div>
  )
}
