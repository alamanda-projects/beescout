'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getMyApprovals } from '@/lib/api/contracts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { ClipboardList, CheckCircle2, XCircle, Clock, ChevronDown, ChevronUp } from 'lucide-react'
import type { ApprovalRecord } from '@/types/contract'

function StatusBadge({ status }: { status: string }) {
  if (status === 'approved') return <Badge variant="success">Disetujui</Badge>
  if (status === 'rejected') return <Badge variant="destructive">Ditolak</Badge>
  return <Badge variant="warning">Menunggu</Badge>
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'approved') return <CheckCircle2 size={16} className="text-emerald-500" />
  if (status === 'rejected') return <XCircle size={16} className="text-red-400" />
  return <Clock size={16} className="text-amber-500" />
}

function VoteList({ record }: { record: ApprovalRecord }) {
  const [open, setOpen] = useState(false)
  const voted = record.votes.length
  const total = record.approvers.length

  return (
    <div>
      <button
        onClick={() => setOpen((p) => !p)}
        className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 transition-colors"
      >
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        {voted}/{total} approver sudah vote
      </button>
      {open && (
        <div className="mt-2 space-y-1.5 pl-2 border-l-2 border-slate-100">
          {record.approvers.map((approver) => {
            const vote = record.votes.find((v) => v.username === approver)
            return (
              <div key={approver} className="flex items-center gap-2 text-xs text-slate-600">
                {vote ? (
                  vote.vote === 'approved'
                    ? <CheckCircle2 size={12} className="text-emerald-500 shrink-0" />
                    : <XCircle size={12} className="text-red-400 shrink-0" />
                ) : (
                  <Clock size={12} className="text-amber-400 shrink-0" />
                )}
                <span className="font-medium">{approver}</span>
                {vote?.reason && <span className="text-muted-foreground">— {vote.reason}</span>}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function MyApprovalsPage() {
  const { data: approvals = [], isLoading } = useQuery({
    queryKey: ['my-approvals'],
    queryFn: getMyApprovals,
  })

  const pending = approvals.filter((a) => a.status === 'pending')
  const resolved = approvals.filter((a) => a.status !== 'pending')

  function renderList(list: ApprovalRecord[]) {
    return (
      <div className="space-y-3">
        {list.map((record) => (
          <Card key={record.approval_id}>
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-2">
                  <StatusIcon status={record.status} />
                  <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
                    {record.contract_number}
                  </code>
                  <StatusBadge status={record.status} />
                </div>
                {record.created_at && (
                  <span className="text-xs text-muted-foreground">
                    {new Date(record.created_at).toLocaleString('id-ID')}
                  </span>
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-0 space-y-2">
              <VoteList record={record} />
              {record.resolved_at && (
                <p className="text-xs text-muted-foreground">
                  Diselesaikan: {new Date(record.resolved_at).toLocaleString('id-ID')}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-5 max-w-3xl">
        <Skeleton className="h-8 w-64" />
        {[1, 2, 3].map((i) => <Skeleton key={i} className="h-28 w-full" />)}
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Pengajuan Perubahan Saya</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Status perubahan kontrak yang telah Anda ajukan
        </p>
      </div>

      {approvals.length === 0 ? (
        <Card>
          <CardContent className="py-14 text-center text-muted-foreground">
            <ClipboardList size={36} className="mx-auto mb-3 opacity-25" />
            <p className="text-sm font-medium">Belum ada pengajuan perubahan</p>
            <p className="text-xs mt-1">Edit kontrak yang Anda kelola untuk membuat pengajuan</p>
          </CardContent>
        </Card>
      ) : (
        <>
          {pending.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-700">Menunggu Persetujuan ({pending.length})</h3>
              {renderList(pending)}
            </div>
          )}
          {resolved.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-700">Riwayat ({resolved.length})</h3>
              {renderList(resolved)}
            </div>
          )}
        </>
      )}
    </div>
  )
}
