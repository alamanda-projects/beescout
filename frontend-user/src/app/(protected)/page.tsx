'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { getMe } from '@/lib/api/auth'
import { getContracts } from '@/lib/api/contracts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { FileText, ArrowRight, Building2, Tag } from 'lucide-react'
import { ROLE_LABELS } from '@/types/user'
import type { Contract } from '@/types/contract'

function StatCard({
  title,
  value,
  icon: Icon,
  loading,
}: {
  title: string
  value: string | number
  icon: React.ElementType
  loading?: boolean
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 pt-6">
        <div className="p-2.5 bg-indigo-50 rounded-lg">
          <Icon size={20} className="text-indigo-600" />
        </div>
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          {loading ? (
            <Skeleton className="h-7 w-12 mt-1" />
          ) : (
            <p className="text-2xl font-bold">{value}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function ContractTypeCount({ contracts }: { contracts: Contract[] }) {
  const counts = contracts.reduce<Record<string, number>>((acc, c) => {
    const type = c.metadata?.type ?? 'Lainnya'
    acc[type] = (acc[type] ?? 0) + 1
    return acc
  }, {})

  return (
    <div className="flex flex-wrap gap-2">
      {Object.entries(counts).map(([type, count]) => (
        <Badge key={type} variant="secondary" className="gap-1.5">
          <span className="capitalize">{type}</span>
          <span className="bg-white text-slate-700 rounded-full px-1.5 text-xs">{count}</span>
        </Badge>
      ))}
    </div>
  )
}

export default function DashboardPage() {
  const { data: user, isLoading: userLoading } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
  })

  const { data: contracts = [], isLoading: contractsLoading } = useQuery({
    queryKey: ['contracts'],
    queryFn: () => getContracts(),
  })

  const recentContracts = contracts.slice(0, 5)

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Welcome */}
      <div>
        <h2 className="text-xl font-semibold text-slate-900">
          {userLoading ? (
            <Skeleton className="h-7 w-48 inline-block" />
          ) : (
            <>Selamat datang, {user?.client_id} 👋</>
          )}
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          {userLoading ? (
            <Skeleton className="h-4 w-64 mt-1" />
          ) : (
            <>
              Domain: <span className="font-medium text-slate-700">{user?.data_domain}</span>
              {' · '}
              Peran: <span className="font-medium text-slate-700">{ROLE_LABELS[user?.group_access ?? ''] ?? user?.group_access}</span>
            </>
          )}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Total Data Contract"
          value={contractsLoading ? '...' : contracts.length}
          icon={FileText}
          loading={contractsLoading}
        />
        <StatCard
          title="Domain"
          value={user?.data_domain ?? '...'}
          icon={Building2}
          loading={userLoading}
        />
        <Card>
          <CardContent className="flex items-center gap-4 pt-6">
            <div className="p-2.5 bg-indigo-50 rounded-lg">
              <Tag size={20} className="text-indigo-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-muted-foreground">Tipe Kontrak</p>
              {contractsLoading ? (
                <Skeleton className="h-5 w-24 mt-1" />
              ) : (
                <div className="mt-1">
                  <ContractTypeCount contracts={contracts} />
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Contracts */}
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
          {contractsLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : recentContracts.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">
              <FileText size={32} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">Belum ada data contract yang tersedia.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {recentContracts.map((c) => (
                <Link
                  key={c.contract_number}
                  href={`/contracts/${c.contract_number}`}
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 transition-colors group"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">{c.metadata?.name}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {c.contract_number} · {c.metadata?.owner}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 ml-4 shrink-0">
                    <Badge variant="secondary" className="capitalize text-xs">
                      {c.metadata?.type}
                    </Badge>
                    <ArrowRight size={14} className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
