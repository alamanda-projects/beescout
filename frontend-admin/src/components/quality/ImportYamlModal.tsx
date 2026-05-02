'use client'

/**
 * ImportYamlModal
 * Modal untuk import data contract dari file YAML.
 * State: idle → validating → error / success
 *
 * Posisi tombol pemicu (konsisten di 3 lokasi):
 *   - Halaman daftar kontrak (di sebelah tombol "Buat Baru")
 *   - Halaman detail kontrak (di sebelah tombol "Edit")
 *   - Form buat kontrak baru (sebagai shortcut "Isi dari YAML")
 *
 * Hanya root dan admin yang melihat tombol ini
 * (filter berdasarkan prop userRole).
 */

import { useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { validateYaml, importYaml } from '@/lib/api/catalog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { toast } from 'sonner'
import { Upload, X, CheckCircle2, AlertCircle, Loader2, FileText, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { YamlValidationResult } from '@/types/rule_catalog'

// ─── Types ─────────────────────────────────────────────────────────────────────

type ModalState = 'idle' | 'validating' | 'error' | 'success'
type ImportContext = 'list' | 'detail' | 'new'

interface Props {
  /** Konteks menentukan label tombol dan perilaku setelah import */
  context?: ImportContext
  /** Nomor kontrak — digunakan di context='detail' untuk update */
  contractNumber?: string
  /** Jika ada callback (misal: prefill form baru), gunakan ini */
  onPrefill?: (data: Record<string, unknown>) => void
  /** Role user — tombol hanya tampil untuk root dan admin */
  userRole: 'root' | 'admin' | 'developer' | 'user'
}

// ─── Trigger button ────────────────────────────────────────────────────────────

export function ImportYamlButton({
  context = 'list',
  contractNumber,
  onPrefill,
  userRole,
}: Props) {
  const [open, setOpen] = useState(false)

  // Sembunyikan untuk developer dan user
  if (userRole === 'developer' || userRole === 'user') return null

  const label = context === 'new' ? 'Isi dari YAML' : 'Import YAML'

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        className="gap-1.5 border-amber-300 text-amber-700 bg-amber-50 hover:bg-amber-100 hover:border-amber-400"
        onClick={() => setOpen(true)}
      >
        <Upload size={13} />
        {label}
      </Button>

      {open && (
        <ImportYamlModal
          context={context}
          contractNumber={contractNumber}
          onPrefill={onPrefill}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  )
}

// ─── Modal ─────────────────────────────────────────────────────────────────────

interface ModalProps {
  context: ImportContext
  contractNumber?: string
  onPrefill?: (data: Record<string, unknown>) => void
  onClose: () => void
}

function ImportYamlModal({ context, contractNumber, onPrefill, onClose }: ModalProps) {
  const router = useRouter()
  const fileRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [pasteText, setPasteText] = useState('')
  const [drag, setDrag] = useState(false)
  const [modalState, setModalState] = useState<ModalState>('idle')
  const [result, setResult] = useState<YamlValidationResult | null>(null)
  const [importing, setImporting] = useState(false)

  // ── File handling ────────────────────────────────────────────────────────────
  const handleFile = useCallback((f: File) => {
    if (!f.name.endsWith('.yaml') && !f.name.endsWith('.yml')) {
      toast.error('Hanya file .yaml atau .yml yang diterima.')
      return
    }
    if (f.size > 5 * 1024 * 1024) {
      toast.error('Ukuran file maksimal 5 MB.')
      return
    }
    setFile(f)
    setPasteText('')
  }, [])

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDrag(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  // ── Validate ─────────────────────────────────────────────────────────────────
  const handleValidate = async () => {
    let targetFile = file

    // Build file from pasted text if no file selected
    if (!targetFile && pasteText.trim()) {
      const blob = new Blob([pasteText], { type: 'text/yaml' })
      targetFile = new File([blob], 'contract.yaml', { type: 'text/yaml' })
    }

    if (!targetFile) {
      toast.error('Pilih file atau tempel isi YAML terlebih dahulu.')
      return
    }

    setModalState('validating')
    setResult(null)

    try {
      const res = await validateYaml(targetFile)
      setResult(res)
      setModalState(res.valid ? 'success' : 'error')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(msg ?? 'Gagal memvalidasi file.')
      setModalState('idle')
    }
  }

  // ── Import / prefill ──────────────────────────────────────────────────────────
  const handleConfirm = async () => {
    if (!result?.valid || !result.summary) return

    // context='new' → prefill form, jangan import langsung
    if (context === 'new' && onPrefill) {
      onPrefill(result.summary.raw)
      toast.success('Form berhasil diisi dari YAML.')
      onClose()
      return
    }

    // context='list' atau 'detail' → import ke database
    let targetFile = file
    if (!targetFile && pasteText.trim()) {
      const blob = new Blob([pasteText], { type: 'text/yaml' })
      targetFile = new File([blob], 'contract.yaml', { type: 'text/yaml' })
    }
    if (!targetFile) return

    setImporting(true)
    try {
      const saved = await importYaml(targetFile)
      toast.success(`Kontrak "${saved.metadata?.name}" berhasil diimport.`)
      onClose()
      router.push(`/contracts/${saved.contract_number}`)
      router.refresh()
    } catch (err: unknown) {
      const detail = (err as any)?.response?.data?.detail
      let msg = 'Gagal mengimport kontrak.'
      if (typeof detail === 'string') msg = detail
      else if (Array.isArray(detail)) msg = detail.map((e: { msg?: string }) => e.msg ?? JSON.stringify(e)).join('; ')
      toast.error(msg)
    } finally {
      setImporting(false)
    }
  }

  // ── Render ───────────────────────────────────────────────────────────────────
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div className="flex items-center gap-2">
            <Upload size={16} className="text-amber-500" />
            <span className="font-semibold text-sm">
              {context === 'new' ? 'Isi Form dari File YAML' : 'Import Data Contract dari YAML'}
            </span>
          </div>
          <button onClick={onClose} className="rounded p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700">
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-4">

          {/* Info banner */}
          <div className="flex gap-2 rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-xs text-blue-800">
            <AlertCircle size={13} className="shrink-0 mt-0.5" />
            File harus berformat YAML dan sesuai standar Open Data Contract Standard (ODCS). Validasi dijalankan otomatis sebelum import.
          </div>

          {/* Upload zone — idle only */}
          {(modalState === 'idle' || modalState === 'validating') && (
            <>
              <div
                className={cn(
                  'rounded-lg border-2 border-dashed p-8 text-center cursor-pointer transition-colors',
                  drag ? 'border-amber-400 bg-amber-50' : 'border-zinc-300 hover:border-amber-300 hover:bg-amber-50/50',
                  file ? 'border-solid border-green-400 bg-green-50' : '',
                )}
                onClick={() => fileRef.current?.click()}
                onDragOver={e => { e.preventDefault(); setDrag(true) }}
                onDragLeave={() => setDrag(false)}
                onDrop={handleDrop}
              >
                <input
                  ref={fileRef}
                  type="file"
                  accept=".yaml,.yml"
                  className="hidden"
                  onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
                />
                {file ? (
                  <>
                    <FileText size={28} className="mx-auto mb-2 text-green-600" />
                    <p className="text-sm font-semibold text-green-700">{file.name}</p>
                    <p className="text-xs text-green-600 mt-1">{(file.size / 1024).toFixed(1)} KB · siap divalidasi</p>
                  </>
                ) : (
                  <>
                    <Upload size={28} className="mx-auto mb-2 text-zinc-400" />
                    <p className="text-sm font-semibold text-zinc-700">Seret file di sini, atau klik untuk pilih</p>
                    <p className="text-xs text-zinc-400 mt-1">Format: .yaml · Maksimal 5 MB</p>
                  </>
                )}
              </div>

              <div className="flex items-center gap-3">
                <Separator className="flex-1" />
                <span className="text-xs text-zinc-400">atau tempel isi file</span>
                <Separator className="flex-1" />
              </div>

              <textarea
                value={pasteText}
                onChange={e => { setPasteText(e.target.value); setFile(null) }}
                rows={5}
                placeholder={'standard_version: 0.0.0\ncontract_number: ...\nmetadata:\n  name: ...'}
                className="w-full rounded-md border border-zinc-200 bg-zinc-50 p-3 font-mono text-xs text-zinc-700 resize-none focus:outline-none focus:border-amber-400"
              />
            </>
          )}

          {/* Validating spinner */}
          {modalState === 'validating' && (
            <div className="flex flex-col gap-2">
              {['Format YAML valid', 'Struktur data contract terdeteksi', 'Validasi schema ODCS...'].map((s, i) => (
                <div key={i} className="flex items-center gap-3 rounded-md border px-3 py-2 text-sm border-zinc-200">
                  {i < 2
                    ? <CheckCircle2 size={14} className="text-green-500 shrink-0" />
                    : <Loader2 size={14} className="animate-spin text-amber-500 shrink-0" />}
                  <span className={i < 2 ? 'font-medium' : 'text-zinc-500'}>{s}</span>
                </div>
              ))}
            </div>
          )}

          {/* Error state */}
          {modalState === 'error' && result && (
            <div className="flex flex-col gap-3">
              <div className="flex gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-xs text-red-800">
                <AlertCircle size={14} className="shrink-0 mt-0.5" />
                <div>
                  <strong>{result.errors?.length} masalah ditemukan</strong>
                  <p className="mt-0.5">File tidak bisa diimport sampai semua masalah diperbaiki.</p>
                </div>
              </div>

              {/* Error list */}
              <div className="rounded-md bg-zinc-950 p-3 font-mono text-[11px] leading-7 max-h-40 overflow-y-auto">
                {result.errors?.map((e, i) => (
                  <div key={i}>
                    <span className="text-red-400">✗ {e.field ?? `baris ${e.line ?? '?'}`}</span>
                    <span className="text-zinc-500 ml-1">— {e.message}</span>
                  </div>
                ))}
              </div>

              {/* Suggestions */}
              {result.suggestions && result.suggestions.filter(Boolean).length > 0 && (
                <div className="flex flex-col gap-2">
                  <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Saran Perbaikan</p>
                  {result.suggestions.filter(Boolean).map((s, i) => (
                    <div key={i} className="flex gap-2.5 rounded-md border border-zinc-200 p-2.5">
                      <div className="h-5 w-5 shrink-0 rounded-full bg-amber-500 text-white text-[10px] font-bold flex items-center justify-center">{i + 1}</div>
                      <p className="text-xs text-zinc-700 leading-relaxed">{s}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Success state */}
          {modalState === 'success' && result?.summary && (
            <div className="flex flex-col gap-3">
              <div className="flex gap-2 rounded-md border border-green-200 bg-green-50 px-3 py-2.5 text-xs text-green-800">
                <CheckCircle2 size={14} className="shrink-0 mt-0.5" />
                <div>
                  <strong>Semua validasi lolos.</strong>
                  <p className="mt-0.5">Periksa ringkasan di bawah sebelum mengkonfirmasi.</p>
                </div>
              </div>

              {/* Warnings */}
              {result.warnings && result.warnings.length > 0 && result.warnings.map((w, i) => (
                <div key={i} className="flex gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                  <AlertTriangle size={12} className="shrink-0 mt-0.5" />{w.message}
                </div>
              ))}

              {/* Summary table */}
              <div className="rounded-lg border border-zinc-200 overflow-hidden">
                <div className="bg-zinc-50 px-4 py-2.5 border-b text-xs font-semibold text-zinc-600">
                  Ringkasan yang Akan Diimport
                </div>
                <div className="px-4 py-3 grid grid-cols-2 gap-x-8 gap-y-2">
                  {[
                    ['Nama Kontrak', result.summary.contract_name],
                    ['Pemilik',      result.summary.owner],
                    ['Jenis',        result.summary.type],
                    ['Versi',        result.summary.version],
                    ['Jumlah Kolom', `${result.summary.columns} kolom`],
                    ['Aturan Kualitas', `Dataset: ${result.summary.dataset_quality_rules} · Kolom: ${result.summary.column_quality_rules}`],
                    ['Pemangku',     `${result.summary.stakeholders} orang`],
                    ['Nomor Kontrak', result.summary.has_contract_number ? 'Dari file' : 'Digenerate otomatis'],
                  ].map(([k, v]) => (
                    <div key={k} className="flex gap-2 text-xs">
                      <span className="text-zinc-400 shrink-0 w-28">{k}</span>
                      <span className="font-medium text-zinc-800">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 border-t px-5 py-3">
          <Button variant="outline" size="sm" onClick={onClose}>Batal</Button>

          {(modalState === 'idle') && (
            <Button
              size="sm"
              className="bg-amber-500 hover:bg-amber-600 text-white gap-1.5"
              onClick={handleValidate}
              disabled={!file && !pasteText.trim()}
            >
              <Loader2 size={12} className="hidden" />
              Validasi &amp; Lanjutkan
            </Button>
          )}

          {modalState === 'error' && (
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5 border-amber-300 text-amber-700"
              onClick={() => { setModalState('idle'); setResult(null); setFile(null); setPasteText('') }}
            >
              <Upload size={12} /> Coba File Lain
            </Button>
          )}

          {modalState === 'success' && (
            <Button
              size="sm"
              className="bg-amber-500 hover:bg-amber-600 text-white gap-1.5"
              onClick={handleConfirm}
              disabled={importing}
            >
              {importing && <Loader2 size={12} className="animate-spin" />}
              {context === 'new' ? 'Isi Form' : 'Konfirmasi Import'}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
