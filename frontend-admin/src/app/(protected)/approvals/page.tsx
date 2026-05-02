'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPendingApprovals, castVote } from '@/lib/api/admin'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { CheckCircle2, XCircle, ClipboardList, ChevronDown, ChevronUp } from 'lucide-react'
import { toast } from 'sonner'
import type { ApprovalRecord } from '@/types/contract'

function ApprovalStatusBadge({ status }: { status: string }) {
  if (status === 'approved') return <Badge variant="success">Disetujui</Badge>
  if (status === 'rejected') return <Badge variant="destructive">Ditolak</Badge>
  return <Badge variant="warning">Menunggu</Badge>
}

function VoteProgress({ record }: { record: ApprovalRecord }) {
  const approved = record.votes.filter((v) => v.vote === 'approved').length
  const rejected = record.votes.filter((v) => v.vote === 'rejected').length
  const total = record.approvers.length
  return (
    <p className="text-xs text-muted-foreground">
      {approved}/{total} setuju · {rejected} menolak · {total - record.votes.length} belum vote
    </p>
  )
}

function ChangesPreview({ changes }: { changes: Record<string, unknown> }) {
  const [open, setOpen] = useState(false)
  const preview = JSON.stringify(changes, null, 2)
  return (
    <div>
      <button
        onClick={() => setOpen((p) => !p)}
        className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 transition-colors"
      >
        {open ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        {open ? 'Sembunyikan' : 'Lihat'} perubahan yang diajukan
      </button>
      {open && (
        <pre className="mt-2 text-xs bg-slate-50 border rounded p-3 overflow-x-auto max-h-64 text-slate-700">
          {preview}
        </pre>
      )}
    </div>
  )
}

export default function ApprovalsPage() {
  const queryClient = useQueryClient()
  const [voteTarget, setVoteTarget] = useState<{ record: ApprovalRecord; type: 'approved' | 'rejected' } | null>(null)
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
      setVoteTarget(null)
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

  function handleVote() {
    if (!voteTarget) return
    submitVote({ id: voteTarget.record.approval_id, vote: voteTarget.type, reason: reason || undefined })
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
          {approvals.map((record) => (
            <Card key={record.approval_id}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <CardTitle className="text-sm">
                        <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs text-slate-600">
                          {record.contract_number}
                        </code>
                      </CardTitle>
                      <ApprovalStatusBadge status={record.status} />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Diajukan oleh <span className="font-medium text-slate-700">{record.requested_by}</span>
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
                      onClick={() => { setVoteTarget({ record, type: 'rejected' }); setReason('') }}
                    >
                      <XCircle size={14} className="mr-1" /> Tolak
                    </Button>
                    <Button
                      size="sm"
                      className="bg-emerald-600 hover:bg-emerald-700"
                      onClick={() => { setVoteTarget({ record, type: 'approved' }); setReason('') }}
                    >
                      <CheckCircle2 size={14} className="mr-1" /> Setuju
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0 space-y-3">
                <VoteProgress record={record} />
                {record.votes.length > 0 && (
                  <div className="space-y-1">
                    {record.votes.map((v) => (
                      <div key={v.username} className="flex items-center gap-2 text-xs text-slate-600">
                        {v.vote === 'approved'
                          ? <CheckCircle2 size={12} className="text-emerald-500 shrink-0" />
                          : <XCircle size={12} className="text-red-400 shrink-0" />}
                        <span className="font-medium">{v.username}</span>
                        {v.reason && <span className="text-muted-foreground">— {v.reason}</span>}
                      </div>
                    ))}
                  </div>
                )}
                <ChangesPreview changes={record.proposed_changes} />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={!!voteTarget} onOpenChange={(o) => { if (!o) { setVoteTarget(null); setReason('') } }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {voteTarget?.type === 'approved' ? 'Konfirmasi Persetujuan' : 'Konfirmasi Penolakan'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <p className="text-sm text-muted-foreground">
              {voteTarget?.type === 'approved'
                ? 'Anda akan menyetujui perubahan kontrak ini. Jika semua approver setuju, perubahan akan langsung diterapkan.'
                : 'Anda akan menolak perubahan kontrak ini. Perubahan akan dibatalkan segera.'}
            </p>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-700">
                Alasan {voteTarget?.type === 'rejected' ? '(wajib)' : '(opsional)'}
              </label>
              <Textarea
                placeholder="Tulis alasan Anda..."
                className="text-sm resize-none"
                rows={3}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setVoteTarget(null); setReason('') }}>
              Batal
            </Button>
            <Button
              disabled={isPending || (voteTarget?.type === 'rejected' && !reason.trim())}
              className={voteTarget?.type === 'approved' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-red-600 hover:bg-red-700'}
              onClick={handleVote}
            >
              {isPending ? 'Menyimpan...' : voteTarget?.type === 'approved' ? 'Setuju' : 'Tolak'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
