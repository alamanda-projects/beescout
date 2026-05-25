'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPendingApprovals, castVote } from '@/lib/api/admin'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { CheckCircle2, XCircle, ClipboardList, ChevronDown, ChevronUp, Clock, AlertTriangle } from 'lucide-react'
import { toast } from 'sonner'
import { APPROVER_ROLE_LABELS, type ApprovalRecord } from '@/types/contract'

// Tampilkan kunci peran sesuai urutan preferensi (owner > producer > consumer),
// dengan kunci legacy ('steward') ditempatkan setelahnya. Kunci tak dikenal di
// akhir, alfabetis — supaya UI tetap stabil bila approval lama format ADR-0004
// muncul di sini (kunci 'steward'). Lihat ADR-0005.
const ROLE_ORDER = ['owner', 'producer', 'consumer', 'steward'] as const
function orderRoleKeys(keys: string[]): string[] {
  const indexed = (k: string) => {
    const i = (ROLE_ORDER as readonly string[]).indexOf(k)
    return i === -1 ? Number.MAX_SAFE_INTEGER : i
  }
  return [...keys].sort((a, b) => indexed(a) - indexed(b) || a.localeCompare(b))
}
function roleLabel(role: string): string {
  return APPROVER_ROLE_LABELS[role as keyof typeof APPROVER_ROLE_LABELS]
    ?? (role.charAt(0).toUpperCase() + role.slice(1))
}

function StatusBadge({ status }: { status: string }) {
  if (status === 'approved') return <Badge variant="success">Disetujui</Badge>
  if (status === 'rejected') return <Badge variant="destructive">Ditolak</Badge>
  return <Badge variant="warning">Menunggu</Badge>
}

// ADR-0004 — progres per peran (steward/producer/consumer). Bila approval
// lama (tanpa approvers_by_role), jatuh ke summary flat seperti sebelumnya.
function RoleProgress({ record }: { record: ApprovalRecord }) {
  const byRole = record.approvers_by_role
  if (!byRole) {
    const approved = record.votes.filter((v) => v.vote === 'approved').length
    const rejected = record.votes.filter((v) => v.vote === 'rejected').length
    const total = record.approvers.length
    return (
      <p className="text-xs text-muted-foreground">
        {approved}/{total} setuju · {rejected} menolak · {total - record.votes.length} belum vote
      </p>
    )
  }

  const approvedSet = new Set(record.votes.filter((v) => v.vote === 'approved').map((v) => v.username))
  const rejectedSet = new Set(record.votes.filter((v) => v.vote === 'rejected').map((v) => v.username))
  // Iterasi sesuai kunci yang ada di doc + fallback_roles (peran kosong tetap
  // ditampilkan supaya operator melihat alasan auto-pass).
  const presentKeys = Object.keys(byRole)
  const fallbackKeys = (record.fallback_roles ?? []).filter((r) => !presentKeys.includes(r))
  const roles = orderRoleKeys([...presentKeys, ...fallbackKeys])

  return (
    <div className="space-y-1.5">
      {roles.map((role) => {
        const users = byRole[role] ?? []
        const isFallback = users.length === 0
        const anyApproved = users.some((u) => approvedSet.has(u))
        const anyRejected = users.some((u) => rejectedSet.has(u))
        const Icon = isFallback ? AlertTriangle
                    : anyRejected ? XCircle
                    : anyApproved ? CheckCircle2
                    : Clock
        const tone = isFallback ? 'text-amber-500'
                    : anyRejected ? 'text-red-500'
                    : anyApproved ? 'text-emerald-500'
                    : 'text-amber-500'
        return (
          <div key={role} className="flex items-start gap-2 text-xs">
            <Icon size={14} className={`${tone} shrink-0 mt-0.5`} />
            <div className="flex-1">
              <span className="font-medium text-slate-700">{roleLabel(role)}</span>
              {isFallback ? (
                <span className="text-muted-foreground italic"> — tidak ada (auto-pass)</span>
              ) : (
                <>
                  <span className="text-muted-foreground"> ({users.filter((u) => approvedSet.has(u)).length}/{users.length})</span>
                  <div className="flex flex-wrap gap-x-2 gap-y-0.5 mt-0.5">
                    {users.map((u) => {
                      const voted = approvedSet.has(u) ? 'approved' : rejectedSet.has(u) ? 'rejected' : null
                      return (
                        <span key={u} className={
                          voted === 'approved' ? 'text-emerald-700'
                          : voted === 'rejected' ? 'text-red-600'
                          : 'text-slate-500'
                        }>
                          {voted === 'approved' ? '✓' : voted === 'rejected' ? '✕' : '⋯'} @{u}
                        </span>
                      )
                    })}
                  </div>
                </>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function FallbackBanner({ roles }: { roles?: string[] }) {
  if (!roles || roles.length === 0) return null
  return (
    <div className="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-2.5 py-2 text-xs text-amber-800">
      <AlertTriangle size={13} className="mt-0.5 shrink-0" />
      <span>
        Tidak ada approver dari peran <strong>{orderRoleKeys(roles).map(roleLabel).join(', ')}</strong> —
        auto-lulus. Lengkapi <em>username</em> di stakeholder kontrak agar peran ini ikut menyetujui di pengajuan berikutnya.
      </span>
    </div>
  )
}

function ChangesPreview({ changes }: { changes: Record<string, unknown> }) {
  const [open, setOpen] = useState(false)
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((p) => !p)}
        className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 transition-colors"
      >
        {open ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        {open ? 'Sembunyikan' : 'Lihat'} perubahan yang diajukan
      </button>
      {open && (
        <pre className="mt-2 text-xs bg-slate-50 border rounded p-3 overflow-x-auto max-h-64 text-slate-700">
          {JSON.stringify(changes, null, 2)}
        </pre>
      )}
    </div>
  )
}

type VoteState = { approvalId: string; type: 'approved' | 'rejected' } | null

export default function ApprovalsPage() {
  const queryClient = useQueryClient()
  const [voteState, setVoteState] = useState<VoteState>(null)
  const [reason, setReason] = useState('')

  const { data: approvals = [], isLoading } = useQuery({
    queryKey: ['pending-approvals'],
    queryFn: getPendingApprovals,
  })

  const { mutate: submitVote, isPending } = useMutation({
    mutationFn: ({ id, vote, reason }: { id: string; vote: 'approved' | 'rejected'; reason?: string }) =>
      castVote(id, vote, reason),
    onSuccess: (_, vars) => {
      toast.success(vars.vote === 'approved' ? 'Vote setuju berhasil.' : 'Perubahan ditolak.')
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] })
      queryClient.invalidateQueries({ queryKey: ['all-contracts'] })
      setVoteState(null)
      setReason('')
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail
      let msg = 'Gagal menyimpan vote.'
      if (typeof detail === 'string') msg = detail
      else if (Array.isArray(detail)) msg = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
      toast.error(msg)
    },
  })

  function openVote(approvalId: string, type: 'approved' | 'rejected') {
    if (voteState?.approvalId === approvalId && voteState?.type === type) {
      setVoteState(null)
      setReason('')
    } else {
      setVoteState({ approvalId, type })
      setReason('')
    }
  }

  function handleVote() {
    if (!voteState) return
    submitVote({ id: voteState.approvalId, vote: voteState.type, reason: reason || undefined })
  }

  return (
    <div className="space-y-5 max-w-4xl">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Persetujuan Kontrak</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Permintaan perubahan kontrak yang menunggu vote Anda
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-36 w-full" />)}
        </div>
      ) : approvals.length === 0 ? (
        <Card>
          <CardContent className="py-14 text-center text-muted-foreground">
            <ClipboardList size={36} className="mx-auto mb-3 opacity-25" />
            <p className="text-sm font-medium">Tidak ada permintaan yang menunggu vote Anda</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {approvals.map((record) => {
            const isVoting = voteState?.approvalId === record.approval_id
            return (
              <Card key={record.approval_id}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <CardTitle className="text-sm">
                          <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs text-slate-600">
                            {record.target_id ?? record.contract_number ?? '—'}
                          </code>
                        </CardTitle>
                        <Badge variant="outline" className="text-[10px]">
                          {(record.type ?? 'contract_change') === 'rule_catalog_create' ? 'Modul Aturan' : 'Kontrak'}
                        </Badge>
                        <StatusBadge status={record.status} />
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Diajukan oleh{' '}
                        <span className="font-medium text-slate-700">{record.requested_by}</span>
                        {record.created_at && (
                          <> · {new Date(record.created_at).toLocaleString('id-ID')}</>
                        )}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-red-600 border-red-200 hover:bg-red-50"
                        onClick={() => openVote(record.approval_id, 'rejected')}
                      >
                        <XCircle size={14} className="mr-1" /> Tolak
                      </Button>
                      <Button
                        size="sm"
                        className="bg-emerald-600 hover:bg-emerald-700"
                        onClick={() => openVote(record.approval_id, 'approved')}
                      >
                        <CheckCircle2 size={14} className="mr-1" /> Setuju
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0 space-y-3">
                  <RoleProgress record={record} />
                  <FallbackBanner roles={record.fallback_roles} />
                  {record.votes.some((v) => v.reason) && (
                    <div className="space-y-1">
                      {record.votes.filter((v) => v.reason).map((v) => (
                        <div key={v.username} className="flex items-start gap-2 text-xs text-slate-600">
                          {v.vote === 'approved'
                            ? <CheckCircle2 size={12} className="text-emerald-500 shrink-0 mt-0.5" />
                            : <XCircle size={12} className="text-red-400 shrink-0 mt-0.5" />}
                          <span><span className="font-medium">@{v.username}</span> — {v.reason}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <ChangesPreview changes={record.proposed_changes} />

                  {isVoting && (
                    <div className="mt-3 p-4 rounded-lg border bg-slate-50 space-y-3">
                      <p className="text-sm font-medium text-slate-800">
                        {voteState?.type === 'approved'
                          ? 'Konfirmasi: Setujui perubahan ini?'
                          : 'Konfirmasi: Tolak perubahan ini?'}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {voteState?.type === 'approved'
                          ? 'Jika semua approver setuju, perubahan akan langsung diterapkan.'
                          : 'Perubahan akan dibatalkan segera setelah ditolak.'}
                      </p>
                      <div className="space-y-1.5">
                        <label className="text-xs font-medium text-slate-700">
                          Alasan {voteState?.type === 'rejected' ? '(wajib)' : '(opsional)'}
                        </label>
                        <Textarea
                          placeholder="Tulis alasan Anda..."
                          className="text-sm resize-none bg-white"
                          rows={3}
                          value={reason}
                          onChange={(e) => setReason(e.target.value)}
                        />
                      </div>
                      <div className="flex gap-2 justify-end">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => { setVoteState(null); setReason('') }}
                        >
                          Batal
                        </Button>
                        <Button
                          size="sm"
                          disabled={isPending || (voteState?.type === 'rejected' && !reason.trim())}
                          className={
                            voteState?.type === 'approved'
                              ? 'bg-emerald-600 hover:bg-emerald-700'
                              : 'bg-red-600 hover:bg-red-700'
                          }
                          onClick={handleVote}
                        >
                          {isPending
                            ? 'Menyimpan...'
                            : voteState?.type === 'approved'
                            ? 'Ya, Setuju'
                            : 'Ya, Tolak'}
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
