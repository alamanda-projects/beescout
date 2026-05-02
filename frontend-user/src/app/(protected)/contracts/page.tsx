'use client'

import { useState, useMemo, useRef } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { getMyContracts, importYaml } from '@/lib/api/contracts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Search, FileText, ArrowRight, Plus, Upload } from 'lucide-react'
import { toast } from 'sonner'
import type { Contract } from '@/types/contract'

function ContractTypeBadge({ type }: { type?: string }) {
  const variants: Record<string, 'default' | 'info' | 'success' | 'warning' | 'secondary'> = {
    dataset: 'info',
    api: 'success',
    stream: 'warning',
    report: 'secondary',
    model: 'default',
  }
  return (
    <Badge variant={variants[type ?? ''] ?? 'secondary'} className="capitalize">
      {type ?? '-'}
    </Badge>
  )
}

function TableSkeleton() {
  return (
    <div className="space-y-2">
      {[1, 2, 3, 4, 5].map((i) => (
        <Skeleton key={i} className="h-14 w-full" />
      ))}
    </div>
  )
}

export default function ContractsPage() {
  const [search, setSearch] = useState('')
  const [importing, setImporting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()

  const { data: contracts = [], isLoading, refetch } = useQuery({
    queryKey: ['my-contracts'],
    queryFn: getMyContracts,
  })

  async function handleImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setImporting(true)
    try {
      await importYaml(file)
      toast.success('Kontrak berhasil diimpor dari YAML.')
      refetch()
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      let msg = 'Gagal mengimpor YAML.'
      if (typeof detail === 'string') msg = detail
      else if (Array.isArray(detail)) msg = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
      toast.error(msg)
    } finally {
      setImporting(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const filtered = useMemo(() => {
    if (!search.trim()) return contracts
    const q = search.toLowerCase()
    return contracts.filter(
      (c: Contract) =>
        c.contract_number?.toLowerCase().includes(q) ||
        c.metadata?.name?.toLowerCase().includes(q) ||
        c.metadata?.owner?.toLowerCase().includes(q) ||
        c.metadata?.type?.toLowerCase().includes(q)
    )
  }, [contracts, search])

  return (
    <div className="space-y-5 max-w-5xl">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Data Contract</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Kontrak data yang Anda buat atau kelola
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".yaml,.yml"
            className="hidden"
            onChange={handleImport}
          />
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5 border-amber-300 text-amber-700 bg-amber-50 hover:bg-amber-100"
            disabled={importing}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={13} />
            {importing ? 'Mengimpor...' : 'Import YAML'}
          </Button>
          <Button asChild size="sm">
            <Link href="/contracts/new">
              <Plus size={14} className="mr-1" />Tambah Kontrak
            </Link>
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <CardTitle className="text-base">
              {isLoading ? '...' : `${filtered.length} Kontrak`}
            </CardTitle>
            <div className="relative w-full sm:w-64">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Cari nama, nomor, pemilik..."
                className="pl-9 h-9 text-sm"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {isLoading ? (
            <TableSkeleton />
          ) : filtered.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              <FileText size={36} className="mx-auto mb-3 opacity-25" />
              <p className="text-sm font-medium">Tidak ada kontrak ditemukan</p>
              {search && (
                <p className="text-xs mt-1">Coba ubah kata kunci pencarian</p>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nama Kontrak</TableHead>
                  <TableHead>Nomor Kontrak</TableHead>
                  <TableHead>Pemilik</TableHead>
                  <TableHead>Tipe</TableHead>
                  <TableHead>Versi</TableHead>
                  <TableHead className="w-10" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((c: Contract) => (
                  <TableRow key={c.contract_number} className="cursor-pointer">
                    <TableCell>
                      <div className="flex items-center gap-2 flex-wrap">
                        <Link href={`/contracts/${c.contract_number}`}>
                          <span className="font-medium text-slate-900 hover:text-indigo-600 transition-colors">
                            {c.metadata?.name ?? '-'}
                          </span>
                        </Link>
                        {c.approval_status === 'pending' && (
                          <Badge variant="warning" className="text-[10px] py-0 px-1.5">Pending</Badge>
                        )}
                        {c.approval_status === 'rejected' && (
                          <Badge variant="destructive" className="text-[10px] py-0 px-1.5">Ditolak</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
                        {c.contract_number}
                      </code>
                    </TableCell>
                    <TableCell className="text-sm">{c.metadata?.owner ?? '-'}</TableCell>
                    <TableCell>
                      <ContractTypeBadge type={c.metadata?.type} />
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {c.metadata?.version ?? '-'}
                    </TableCell>
                    <TableCell>
                      <Link href={`/contracts/${c.contract_number}`}>
                        <ArrowRight size={15} className="text-muted-foreground hover:text-indigo-600 transition-colors" />
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
