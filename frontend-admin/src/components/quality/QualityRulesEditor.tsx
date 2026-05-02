'use client'

/**
 * QualityRulesEditor
 * Komponen utama untuk mendefinisikan aturan kualitas data (2 layer).
 * Mendukung Mode Bisnis (sentence builder) dan Mode Engineer (form teknis).
 *
 * Props:
 *   - contractNumber: nomor kontrak
 *   - columns: daftar kolom dari model kontrak
 *   - datasetRules: aturan layer 1 (dataset) yang sudah ada
 *   - columnRules: Map<columnName, QualityRule[]> untuk layer 2
 *   - onSave: callback saat user klik Simpan
 *   - userMode: 'biz' | 'eng' — default mode berdasarkan role user
 *   - canSwitchMode: apakah user boleh ganti mode
 */

import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getAllRules } from '@/lib/api/catalog'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { toast } from 'sonner'
import { Plus, Trash2, Code2, User2, ChevronDown, ChevronRight, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  DIMENSION_LABELS, IMPACT_LABELS, IMPACT_BIZ_LABELS, LAYER_LABELS,
  type RuleCatalogItem, type QualityRule, type QualityCustomProp, type ImpactType,
} from '@/types/rule_catalog'

// ─── Types ────────────────────────────────────────────────────────────────────

type UserMode = 'biz' | 'eng'

interface Props {
  contractNumber: string
  columns: { column: string; business_name?: string }[]
  datasetRules: QualityRule[]
  columnRules: Record<string, QualityRule[]>
  onSave: (datasetRules: QualityRule[], columnRules: Record<string, QualityRule[]>) => void
  userMode?: UserMode
  canSwitchMode?: boolean
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const DIMENSION_BADGE: Record<string, string> = {
  completeness: 'bg-green-50 text-green-700 border-green-200',
  validity:     'bg-blue-50 text-blue-700 border-blue-200',
  accuracy:     'bg-amber-50 text-amber-700 border-amber-200',
  security:     'bg-red-50 text-red-700 border-red-200',
}

function buildRuleFromModule(
  module: RuleCatalogItem,
  paramValues: Record<string, string>,
  impact: ImpactType,
  description?: string,
): QualityRule {
  return {
    code: module.code,
    description: description || module.description || '',
    dimension: module.dimension,
    impact,
    custom_properties: module.params
      .filter(p => paramValues[p.key])
      .map(p => ({ property: p.key, value: paramValues[p.key] })),
  }
}

// ─── Mode switcher ────────────────────────────────────────────────────────────

function ModeSwitcher({
  mode, onChange, canSwitch,
}: { mode: UserMode; onChange: (m: UserMode) => void; canSwitch: boolean }) {
  if (!canSwitch) return null
  return (
    <div className="flex items-center gap-1 rounded-lg border border-zinc-200 bg-zinc-100 p-0.5">
      <button
        onClick={() => onChange('biz')}
        className={cn(
          'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all',
          mode === 'biz'
            ? 'bg-amber-500 text-white shadow-sm'
            : 'text-zinc-500 hover:text-zinc-700',
        )}
      >
        <User2 size={12} /> Bisnis
      </button>
      <button
        onClick={() => onChange('eng')}
        className={cn(
          'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all',
          mode === 'eng'
            ? 'bg-zinc-900 text-white shadow-sm'
            : 'text-zinc-500 hover:text-zinc-700',
        )}
      >
        <Code2 size={12} /> Engineer
      </button>
    </div>
  )
}

// ─── Sentence Builder (Mode Bisnis) ───────────────────────────────────────────

function SentenceRuleBuilder({
  modules,
  layer,
  columnName,
  onAdd,
}: {
  modules: RuleCatalogItem[]
  layer: 'dataset' | 'column'
  columnName?: string
  onAdd: (rule: QualityRule) => void
}) {
  const layerModules = modules.filter(
    m => m.layer === layer || m.layer === 'both'
  )
  const [selectedCode, setSelectedCode] = useState(layerModules[0]?.code ?? '')
  const [paramValues, setParamValues] = useState<Record<string, string>>({})
  const [impact, setImpact] = useState<ImpactType>('operational')
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  const selectedModule = layerModules.find(m => m.code === selectedCode)

  const validateParams = useCallback(() => {
    if (!selectedModule) return false
    const errs: Record<string, string> = {}
    for (const p of selectedModule.params) {
      if (!p.required) continue
      const val = paramValues[p.key]
      if (!val || val.trim() === '') {
        errs[p.key] = 'Wajib diisi'
        continue
      }
      if (p.type === 'number') {
        const n = Number(val)
        if (isNaN(n)) { errs[p.key] = 'Harus berupa angka'; continue }
        if (p.min_value !== undefined && n < p.min_value)
          errs[p.key] = `Minimal ${p.min_value}`
        if (p.max_value !== undefined && n > p.max_value)
          errs[p.key] = `Maksimal ${p.max_value}`
      }
    }
    setValidationErrors(errs)
    return Object.keys(errs).length === 0
  }, [selectedModule, paramValues])

  const handleAdd = () => {
    if (!selectedModule) return
    if (!validateParams()) return
    const rule = buildRuleFromModule(selectedModule, paramValues, impact)
    onAdd(rule)
    setParamValues({})
    setValidationErrors({})
  }

  if (layerModules.length === 0) return (
    <p className="text-sm text-zinc-400 py-4 text-center">Tidak ada modul tersedia untuk layer ini.</p>
  )

  return (
    <div className="flex flex-col gap-3">
      {/* Sentence row */}
      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-loose">
        <span className="text-zinc-700">Pastikan</span>
        {layer === 'column' && columnName && (
          <span className="text-zinc-700">kolom <strong>{columnName}</strong></span>
        )}
        {/* Module dropdown */}
        <select
          value={selectedCode}
          onChange={e => { setSelectedCode(e.target.value); setParamValues({}); setValidationErrors({}) }}
          className="rounded border-[1.5px] border-amber-400 bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800 focus:outline-none"
        >
          {layerModules.map(m => (
            <option key={m.code} value={m.code}>{m.label}</option>
          ))}
        </select>

        {/* Inline params */}
        {selectedModule?.params.map(p => (
          <span key={p.key} className="flex items-center gap-1.5">
            {p.type === 'number' && (
              <>
                <span className="text-zinc-600">sebanyak</span>
                <input
                  type="number"
                  value={paramValues[p.key] ?? ''}
                  onChange={e => setParamValues(prev => ({ ...prev, [p.key]: e.target.value }))}
                  placeholder={p.hint ?? '0'}
                  className={cn(
                    'w-20 rounded border px-2 py-1 text-xs',
                    validationErrors[p.key]
                      ? 'border-red-400 bg-red-50 text-red-700'
                      : 'border-amber-300 bg-amber-50 font-semibold text-amber-800',
                  )}
                />
                <span className="text-zinc-600">karakter</span>
              </>
            )}
            {(p.type === 'select' || p.type === 'multi') && (
              <select
                value={paramValues[p.key] ?? ''}
                onChange={e => setParamValues(prev => ({ ...prev, [p.key]: e.target.value }))}
                className={cn(
                  'rounded border-[1.5px] px-2 py-1 text-xs font-semibold focus:outline-none',
                  validationErrors[p.key]
                    ? 'border-red-400 bg-red-50 text-red-700'
                    : 'border-amber-400 bg-amber-100 text-amber-800',
                )}
              >
                <option value="">— pilih —</option>
                {p.options?.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            )}
            {p.type === 'date' && (
              <>
                <span className="text-zinc-600">{p.key === 'min_date' ? 'mulai' : 'hingga'}</span>
                <input
                  type="text"
                  value={paramValues[p.key] ?? ''}
                  onChange={e => setParamValues(prev => ({ ...prev, [p.key]: e.target.value }))}
                  placeholder="YYYY-MM-DD"
                  className="w-28 rounded border border-amber-300 bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-800"
                />
              </>
            )}
          </span>
        ))}
      </div>

      {/* Validation errors */}
      {Object.entries(validationErrors).map(([k, msg]) => (
        <div key={k} className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          <AlertCircle size={12} /> {msg}
        </div>
      ))}

      {/* Impact + add button */}
      <div className="flex items-center gap-4 text-xs">
        <span className="text-zinc-500">Dampak jika dilanggar:</span>
        <div className="flex gap-2">
          {(Object.entries(IMPACT_BIZ_LABELS) as [ImpactType, string][]).map(([v, l]) => (
            <label key={v} className={cn(
              'flex items-center gap-1.5 cursor-pointer rounded border px-2.5 py-1 text-xs transition-all',
              impact === v ? 'border-amber-400 bg-amber-50 font-semibold text-amber-800' : 'border-zinc-200 text-zinc-500',
            )}>
              <input
                type="radio"
                name={`impact-${layer}-${columnName}`}
                checked={impact === v}
                onChange={() => setImpact(v)}
                className="accent-amber-500"
              />
              {l}
            </label>
          ))}
        </div>
        <Button size="sm" className="ml-auto h-7 gap-1 bg-amber-500 hover:bg-amber-600 text-white" onClick={handleAdd}>
          <Plus size={12} /> Tambahkan
        </Button>
      </div>
    </div>
  )
}

// ─── Engineer Form ────────────────────────────────────────────────────────────

function EngRuleForm({
  modules,
  onAdd,
}: {
  modules: RuleCatalogItem[]
  onAdd: (rule: QualityRule) => void
}) {
  const [code, setCode] = useState(modules[0]?.code ?? '')
  const [dimension, setDimension] = useState<string>('completeness')
  const [impact, setImpact] = useState<string>('operational')
  const [description, setDescription] = useState('')
  const [props, setProps] = useState<QualityCustomProp[]>([{ property: '', value: '' }])

  // Auto-fill when module selected
  const syncModule = (c: string) => {
    const m = modules.find(m => m.code === c)
    if (m) {
      setCode(c)
      setDimension(m.dimension)
      setProps(m.params.map(p => ({ property: p.key, value: '' })))
    }
  }

  const handleAdd = () => {
    if (!code.trim()) { toast.error('Code wajib diisi'); return }
    onAdd({
      code,
      description: description || undefined,
      dimension,
      impact,
      custom_properties: props.filter(p => p.property.trim()),
    })
    setDescription('')
    setProps([{ property: '', value: '' }])
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg bg-zinc-950 p-4 font-mono">
      <div className="grid grid-cols-2 gap-3">
        {/* code */}
        <div>
          <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-zinc-500">code *</div>
          <select
            value={code}
            onChange={e => syncModule(e.target.value)}
            className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-sky-500"
          >
            {modules.map(m => <option key={m.code} value={m.code}>{m.code}</option>)}
          </select>
        </div>
        {/* dimension */}
        <div>
          <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-zinc-500">dimension *</div>
          <select
            value={dimension}
            onChange={e => setDimension(e.target.value)}
            className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-sky-500"
          >
            {Object.entries(DIMENSION_LABELS).map(([v, l]) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
        </div>
      </div>
      {/* description */}
      <div>
        <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-zinc-500">description</div>
        <input
          value={description}
          onChange={e => setDescription(e.target.value)}
          className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-sky-500"
          placeholder="ensure column is not null..."
        />
      </div>
      {/* impact */}
      <div>
        <div className="mb-1 text-[10px] font-bold uppercase tracking-wider text-zinc-500">impact</div>
        <select
          value={impact}
          onChange={e => setImpact(e.target.value)}
          className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-sky-500"
        >
          {Object.entries(IMPACT_LABELS).map(([v, l]) => (
            <option key={v} value={v}>{v}</option>
          ))}
        </select>
      </div>
      {/* custom_properties */}
      <div>
        <div className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-zinc-500">custom_properties</div>
        <div className="flex flex-col gap-1.5">
          {props.map((p, i) => (
            <div key={i} className="grid grid-cols-[1fr_1fr_auto] gap-2 items-center">
              <input
                value={p.property}
                onChange={e => setProps(prev => prev.map((x, j) => j === i ? { ...x, property: e.target.value } : x))}
                placeholder="property"
                className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-xs text-sky-300 focus:outline-none"
              />
              <input
                value={String(p.value)}
                onChange={e => setProps(prev => prev.map((x, j) => j === i ? { ...x, value: e.target.value } : x))}
                placeholder="value"
                className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-xs text-green-300 focus:outline-none"
              />
              <button
                onClick={() => setProps(prev => prev.filter((_, j) => j !== i))}
                className="text-zinc-600 hover:text-red-400 text-sm"
              >×</button>
            </div>
          ))}
          <button
            onClick={() => setProps(prev => [...prev, { property: '', value: '' }])}
            className="flex items-center gap-1.5 text-[11px] text-zinc-600 hover:text-sky-400 border border-dashed border-zinc-700 rounded px-2 py-1 w-fit"
          >
            <Plus size={10} /> custom_property
          </button>
        </div>
      </div>
      <div className="flex justify-end pt-1">
        <button
          onClick={handleAdd}
          className="flex items-center gap-1.5 rounded bg-zinc-800 hover:bg-zinc-700 border border-zinc-600 text-zinc-200 text-xs px-3 py-1.5"
        >
          <Plus size={11} /> Tambah Rule
        </button>
      </div>
    </div>
  )
}

// ─── Rule list ─────────────────────────────────────────────────────────────────

function RuleList({
  rules,
  mode,
  onRemove,
}: { rules: QualityRule[]; mode: UserMode; onRemove: (idx: number) => void }) {
  if (rules.length === 0) return (
    <div className="rounded-md border border-dashed border-zinc-200 py-6 text-center text-xs text-zinc-400">
      Belum ada aturan. Buat aturan pertama di atas.
    </div>
  )
  return (
    <div className="flex flex-col gap-2">
      {rules.map((r, i) => (
        <div key={i} className={cn(
          'flex items-start justify-between gap-3 rounded-md border px-3 py-2.5',
          mode === 'eng' ? 'border-zinc-700 bg-zinc-900' : 'border-zinc-200 bg-white',
        )}>
          <div className="flex-1 min-w-0">
            {mode === 'biz' ? (
              <>
                <div className="text-sm font-medium text-zinc-800 mb-1.5">
                  <span className="font-semibold text-amber-700">{r.code}</span>
                  {r.custom_properties && r.custom_properties.length > 0 && (
                    <span className="text-zinc-500 ml-1">
                      — {r.custom_properties.map(p => p.value).join(', ')}
                    </span>
                  )}
                </div>
                <div className="flex gap-1.5 flex-wrap">
                  {r.dimension && (
                    <span className={cn('inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-semibold', DIMENSION_BADGE[r.dimension])}>
                      {DIMENSION_LABELS[r.dimension as keyof typeof DIMENSION_LABELS] ?? r.dimension}
                    </span>
                  )}
                  {r.impact && (
                    <span className="inline-flex items-center rounded border border-zinc-200 bg-zinc-50 px-1.5 py-0.5 text-[10px] font-semibold text-zinc-600">
                      {IMPACT_BIZ_LABELS[r.impact] ?? r.impact}
                    </span>
                  )}
                </div>
              </>
            ) : (
              <div className="font-mono text-xs text-zinc-300">
                <span className="text-sky-400">{r.code}</span>
                <span className="text-zinc-600 mx-1">·</span>
                <span className="text-yellow-300">{r.dimension}</span>
                <span className="text-zinc-600 mx-1">·</span>
                <span className="text-zinc-500">{r.impact}</span>
                {r.custom_properties?.map((p, j) => (
                  <div key={j} className="ml-3 mt-0.5 text-[11px]">
                    <span className="text-sky-300">{p.property}</span>
                    <span className="text-zinc-600">: </span>
                    <span className="text-green-300">{String(p.value)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          <button onClick={() => onRemove(i)} className={cn(
            'shrink-0 p-1 rounded hover:bg-red-50',
            mode === 'eng' ? 'text-zinc-600 hover:text-red-400' : 'text-zinc-400 hover:text-red-500',
          )}>
            <Trash2 size={13} />
          </button>
        </div>
      ))}
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function QualityRulesEditor({
  contractNumber,
  columns,
  datasetRules: initialDataset,
  columnRules: initialColumns,
  onSave,
  userMode = 'biz',
  canSwitchMode = false,
}: Props) {
  const [mode, setMode] = useState<UserMode>(userMode)
  const [activeLayer, setActiveLayer] = useState<'dataset' | 'column'>('dataset')
  const [activeColumn, setActiveColumn] = useState(columns[0]?.column ?? '')
  const [expandedCol, setExpandedCol] = useState<string | null>(columns[0]?.column ?? null)

  const [datasetRules, setDatasetRules] = useState<QualityRule[]>(initialDataset)
  const [columnRules, setColumnRules] = useState<Record<string, QualityRule[]>>(initialColumns)

  const { data: allModules = [] } = useQuery({
    queryKey: ['rule-catalog'],
    queryFn: getAllRules,
  })

  const dsModules  = allModules.filter(m => m.layer === 'dataset' || m.layer === 'both')
  const colModules = allModules.filter(m => m.layer === 'column'  || m.layer === 'both')

  const addDatasetRule = (rule: QualityRule) => setDatasetRules(prev => [...prev, rule])
  const removeDatasetRule = (i: number) => setDatasetRules(prev => prev.filter((_, j) => j !== i))

  const addColumnRule = (col: string, rule: QualityRule) =>
    setColumnRules(prev => ({ ...prev, [col]: [...(prev[col] ?? []), rule] }))
  const removeColumnRule = (col: string, i: number) =>
    setColumnRules(prev => ({ ...prev, [col]: (prev[col] ?? []).filter((_, j) => j !== i) }))

  const handleSave = () => {
    onSave(datasetRules, columnRules)
    toast.success('Aturan kualitas berhasil disimpan.')
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <p className="text-xs text-zinc-500 mt-0.5">
            {LAYER_LABELS[activeLayer]}
            {mode === 'eng' && (
              <span className="ml-2 font-mono text-[10px] text-sky-500">engineer mode</span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ModeSwitcher mode={mode} onChange={setMode} canSwitch={canSwitchMode} />
          <Button size="sm" className="bg-amber-500 hover:bg-amber-600 text-white" onClick={handleSave}>
            Simpan Aturan
          </Button>
        </div>
      </div>

      {/* Layer tabs */}
      <div className="flex border-b border-zinc-200">
        {(['dataset', 'column'] as const).map(l => (
          <button
            key={l}
            onClick={() => setActiveLayer(l)}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
              activeLayer === l
                ? 'border-amber-500 text-zinc-900 font-semibold'
                : 'border-transparent text-zinc-500 hover:text-zinc-700',
            )}
          >
            {l === 'dataset' ? 'Layer 1 — Keseluruhan Dataset' : 'Layer 2 — Per Kolom'}
          </button>
        ))}
      </div>

      {/* Context tip */}
      <div className={cn(
        'rounded-md border px-3 py-2 text-xs flex gap-2',
        activeLayer === 'dataset'
          ? 'bg-blue-50 border-blue-200 text-blue-800'
          : 'bg-amber-50 border-amber-200 text-amber-800',
      )}>
        <AlertCircle size={13} className="shrink-0 mt-0.5" />
        {activeLayer === 'dataset'
          ? 'Aturan berlaku untuk seluruh dataset — bukan per kolom.'
          : 'Aturan berlaku per kolom. Setiap kolom bisa punya aturan berbeda.'}
      </div>

      {/* Dataset layer */}
      {activeLayer === 'dataset' && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Tambah Aturan Dataset</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {mode === 'biz'
              ? <SentenceRuleBuilder modules={dsModules} layer="dataset" onAdd={addDatasetRule} />
              : <EngRuleForm modules={dsModules} onAdd={addDatasetRule} />}
            <Separator />
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
                Aturan Aktif ({datasetRules.length})
              </p>
              <RuleList rules={datasetRules} mode={mode} onRemove={removeDatasetRule} />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Column layer */}
      {activeLayer === 'column' && (
        <div className="flex flex-col gap-2">
          {columns.map(col => {
            const rules = columnRules[col.column] ?? []
            const isOpen = expandedCol === col.column
            return (
              <Card key={col.column} className={cn(isOpen && 'border-amber-200')}>
                {/* Column accordion header */}
                <button
                  className="flex w-full items-center justify-between px-4 py-3 text-left"
                  onClick={() => setExpandedCol(isOpen ? null : col.column)}
                >
                  <div className="flex items-center gap-3">
                    {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    <code className="rounded bg-zinc-100 px-1.5 py-0.5 text-xs">{col.column}</code>
                    <span className="text-sm font-medium">{col.business_name ?? col.column}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {rules.length > 0
                      ? <Badge variant="outline" className="text-green-700 border-green-200 bg-green-50 text-[10px]">{rules.length} aturan</Badge>
                      : <Badge variant="outline" className="text-red-600 border-red-200 bg-red-50 text-[10px]">Belum ada aturan</Badge>}
                  </div>
                </button>

                {isOpen && (
                  <CardContent className="pt-0 flex flex-col gap-4">
                    <Separator />
                    {mode === 'biz'
                      ? <SentenceRuleBuilder modules={colModules} layer="column" columnName={col.column} onAdd={r => addColumnRule(col.column, r)} />
                      : <EngRuleForm modules={colModules} onAdd={r => addColumnRule(col.column, r)} />}
                    <Separator />
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
                        Aturan Kolom ({rules.length})
                      </p>
                      <RuleList rules={rules} mode={mode} onRemove={i => removeColumnRule(col.column, i)} />
                    </div>
                  </CardContent>
                )}
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
