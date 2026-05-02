'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { getMe } from '@/lib/api/auth'
import { getAllContracts } from '@/lib/api/admin'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { FileText, Plus, ArrowRight, Tag, Building2 } from 'lucide-react'
import type { Contract } from '@/types/contract'

function StatCard({ title, value, icon: Icon, loading }: { title: string; value: string | number; icon: React.ElementType; loading?: boolean }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 pt-6">
        <div className="p-2.5 bg-indigo-50 rounded-lg"><Icon size={20} className="text-indigo-600" /></div>
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          {loading ? <Skeleton className="h-7 w-12 mt-1" /> : <p className="text-2xl font-bold">{value}</p>}
        </div>
      </CardContent>
    </Card>
  )
}

export default function AdminDashboardPage() {
  const { data: user } = useQuery({ queryKey: ['me'], queryFn: getMe })
  const { data: contracts = [], isLoading } = useQuery({ queryKey: ['all-contracts'], queryFn: getAllContracts })

  const domains = Array.from(new Set(contracts.map((c: Contract) => c.metadata?.owner).filter(Boolean)))
  const types   = Array.from(new Set(contracts.map((c: Contract) => c.metadata?.type).filter(Boolean)))
  const recent  = contracts.slice(0, 6)

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Dashboard Admin</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Selamat datang, <span className="font-medium text-slate-700">{user?.client_id}</span>
            {' · '}<Badge variant="warning" className="text-xs">{user?.group_access}</Badge>
          </p>
        </div>
        <Button asChild>
          <Link href="/contracts/new"><Plus size={16} className="mr-1" />Tambah Kontrak</Link>
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard title="Total Data Contract" value={isLoading ? '...' : contracts.length} icon={FileText} loading={isLoading} />
        <StatCard title="Total Pemilik" value={isLoading ? '...' : domains.length} icon={Building2} loading={isLoading} />
        <StatCard title="Tipe Kontrak" value={isLoading ? '...' : types.length} icon={Tag} loading={isLoading} />
      </div>

      {/* Recent contracts */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-base">Kontrak Terbaru</CardTitle>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/contracts" className="gap-1 text-indigo-600 hover:text-indigo-700">
              Lihat semua <ArrowRight size={14} />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">{[1,2,3].map(i => <Skeleton key={i} className="h-12 w-full" />)}</div>
          ) : recent.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">
              <FileText size={32} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">Belum ada data contract.</p>
              <Button size="sm" className="mt-3" asChild>
                <Link href="/contracts/new"><Plus size={14} className="mr-1" />Tambah Sekarang</Link>
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nama Kontrak</TableHead>
                  <TableHead>Pemilik</TableHead>
                  <TableHead>Tipe</TableHead>
                  <TableHead className="w-10" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {recent.map((c: Contract) => (
                  <TableRow key={c.contract_number}>
                    <TableCell>
                      <Link href={`/contracts/${c.contract_number}`} className="font-medium hover:text-indigo-600 transition-colors">
                        {c.metadata?.name}
                      </Link>
                      <p className="text-xs text-muted-foreground mt-0.5 font-mono">{c.contract_number}</p>
                    </TableCell>
                    <TableCell className="text-sm">{c.metadata?.owner ?? '-'}</TableCell>
                    <TableCell><Badge variant="secondary" className="capitalize">{c.metadata?.type}</Badge></TableCell>
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
