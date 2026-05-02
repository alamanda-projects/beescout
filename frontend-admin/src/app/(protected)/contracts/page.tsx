'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { getAllContracts } from '@/lib/api/admin'
import { getMe } from '@/lib/api/auth'
import { ImportYamlButton } from '@/components/quality/ImportYamlModal'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Search, Plus, FileText, ArrowRight } from 'lucide-react'
import type { Contract } from '@/types/contract'

const TYPE_VARIANTS: Record<string, 'default' | 'info' | 'success' | 'warning' | 'secondary'> = {
  dataset: 'info', api: 'success', stream: 'warning', report: 'secondary', model: 'default',
}

export default function AdminContractsPage() {
  const [search, setSearch] = useState('')
  const { data: user } = useQuery({ queryKey: ['me'], queryFn: getMe })
  const { data: contracts = [], isLoading } = useQuery({ queryKey: ['all-contracts'], queryFn: getAllContracts })

  const filtered = useMemo(() => {
    if (!search.trim()) return contracts
    const q = search.toLowerCase()
    return contracts.filter((c: Contract) =>
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
          <p className="text-sm text-muted-foreground mt-1">Kelola semua data contract di seluruh domain</p>
        </div>
        <div className="flex items-center gap-2">
          <ImportYamlButton context="list" userRole={user?.group_access as any} />
          <Button asChild>
            <Link href="/contracts/new"><Plus size={16} className="mr-1" />Tambah Kontrak</Link>
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <CardTitle className="text-base">{isLoading ? '...' : `${filtered.length} Kontrak`}</CardTitle>
            <div className="relative w-full sm:w-64">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <Input placeholder="Cari nama, nomor, pemilik..." className="pl-9 h-9 text-sm"
                value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {isLoading ? (
            <div className="space-y-2">{[1,2,3,4,5].map(i => <Skeleton key={i} className="h-14 w-full" />)}</div>
          ) : filtered.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              <FileText size={36} className="mx-auto mb-3 opacity-25" />
              <p className="text-sm font-medium">Tidak ada kontrak ditemukan</p>
              {!search && (
                <Button size="sm" className="mt-4" asChild>
                  <Link href="/contracts/new"><Plus size={14} className="mr-1" />Tambah Kontrak Pertama</Link>
                </Button>
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
                  <TableRow key={c.contract_number}>
                    <TableCell>
                      <Link href={`/contracts/${c.contract_number}`} className="font-medium hover:text-indigo-600 transition-colors">
                        {c.metadata?.name ?? '-'}
                      </Link>
                    </TableCell>
                    <TableCell><code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">{c.contract_number}</code></TableCell>
                    <TableCell className="text-sm">{c.metadata?.owner ?? '-'}</TableCell>
                    <TableCell><Badge variant={TYPE_VARIANTS[c.metadata?.type ?? ''] ?? 'secondary'} className="capitalize">{c.metadata?.type}</Badge></TableCell>
                    <TableCell className="text-sm text-muted-foreground">{c.metadata?.version ?? '-'}</TableCell>
                    <TableCell>
                      <Link href={`/contracts/${c.contract_number}`}>
                        <ArrowRight size={15} className="text-muted-foreground hover:text-indigo-600" />
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
