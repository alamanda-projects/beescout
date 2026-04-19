'use client'

import { useQuery } from '@tanstack/react-query'
import { getMe, getSAKeys } from '@/lib/api/auth'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Key } from 'lucide-react'
import { ROLE_LABELS } from '@/types/user'
import { formatDate } from '@/lib/utils'
import type { SAKey } from '@/types/user'

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex items-center gap-3 py-2">
      <span className="text-sm text-muted-foreground w-40 shrink-0">{label}</span>
      <span className="text-sm font-medium">{value ?? '-'}</span>
    </div>
  )
}

export default function AdminProfilePage() {
  const { data: user, isLoading } = useQuery({ queryKey: ['me'], queryFn: getMe })
  const { data: saData } = useQuery({ queryKey: ['sakeys'], queryFn: getSAKeys })

  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Profil Saya</h2>
        <p className="text-sm text-muted-foreground mt-1">Informasi akun administrator</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          {isLoading ? (
            <div className="space-y-3">{[1,2,3,4].map(i => <Skeleton key={i} className="h-8 w-full" />)}</div>
          ) : (
            <div className="flex items-start gap-5">
              <Avatar className="h-14 w-14">
                <AvatarFallback className="bg-amber-100 text-amber-700 text-xl font-semibold">
                  {user?.client_id?.charAt(0)?.toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-4">
                  <h3 className="text-lg font-semibold">{user?.client_id}</h3>
                  <Badge variant={user?.is_active ? 'success' : 'destructive'}>
                    {user?.is_active ? 'Aktif' : 'Nonaktif'}
                  </Badge>
                  <Badge variant="warning">{ROLE_LABELS[user?.group_access ?? ''] ?? user?.group_access}</Badge>
                </div>
                <Separator className="mb-4" />
                <div className="space-y-0.5">
                  <InfoRow label="Username" value={user?.client_id} />
                  <InfoRow label="Peran" value={ROLE_LABELS[user?.group_access ?? ''] ?? user?.group_access} />
                  <InfoRow label="Domain" value={user?.data_domain} />
                  <InfoRow label="Tipe Akun" value={user?.type === 'user' ? 'Pengguna' : 'Service Account'} />
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {saData?.sakeys && saData.sakeys.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2"><Key size={16} />Service Account Keys</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Client ID</TableHead>
                  <TableHead>Dibuat</TableHead>
                  <TableHead>Kedaluwarsa</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {saData.sakeys.map((key: SAKey) => (
                  <TableRow key={key.client_id}>
                    <TableCell><code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">{key.client_id}</code></TableCell>
                    <TableCell className="text-sm text-muted-foreground">{formatDate(key.generated_at)}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{formatDate(key.expire_at)}</TableCell>
                    <TableCell><Badge variant={key.is_active ? 'success' : 'secondary'}>{key.is_active ? 'Aktif' : 'Nonaktif'}</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
