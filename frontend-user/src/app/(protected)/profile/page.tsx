'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getMe, getSAKeys, createSAKey } from '@/lib/api/auth'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Key, Plus, Copy, CheckCircle2, AlertCircle } from 'lucide-react'
import { ROLE_LABELS } from '@/types/user'
import { formatDate } from '@/lib/utils'
import { toast } from 'sonner'
import type { SAKey } from '@/types/user'

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex items-center gap-3 py-2">
      <span className="text-sm text-muted-foreground w-40 shrink-0">{label}</span>
      <span className="text-sm font-medium text-slate-900">{value ?? '-'}</span>
    </div>
  )
}

export default function ProfilePage() {
  const [newKey, setNewKey] = useState<{ client_id: string; private_key: string } | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [copied, setCopied] = useState(false)

  const { data: user, isLoading: userLoading } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
  })

  const { data: saData, refetch: refetchKeys } = useQuery({
    queryKey: ['sakeys'],
    queryFn: getSAKeys,
    enabled: user?.group_access === 'developer' || user?.group_access === 'admin' || user?.group_access === 'root',
  })

  const handleGenerateKey = async () => {
    setIsGenerating(true)
    try {
      const key = await createSAKey()
      setNewKey(key)
      refetchKeys()
      toast.success('Service account key berhasil dibuat!')
    } catch {
      toast.error('Gagal membuat service account key.')
    } finally {
      setIsGenerating(false)
    }
  }

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
    toast.success('Disalin ke clipboard')
  }

  const canGenerateSAKey = ['developer', 'admin', 'root'].includes(user?.group_access ?? '')

  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Profil Saya</h2>
        <p className="text-sm text-muted-foreground mt-1">Informasi akun dan pengaturan</p>
      </div>

      {/* Profile Card */}
      <Card>
        <CardContent className="pt-6">
          {userLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-8 w-full" />)}
            </div>
          ) : (
            <div className="flex items-start gap-5">
              <Avatar className="h-14 w-14">
                <AvatarFallback className="bg-indigo-100 text-indigo-700 text-xl font-semibold">
                  {user?.client_id?.charAt(0)?.toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-4">
                  <h3 className="text-lg font-semibold">{user?.client_id}</h3>
                  <Badge variant={user?.is_active ? 'success' : 'destructive'}>
                    {user?.is_active ? 'Aktif' : 'Nonaktif'}
                  </Badge>
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

      {/* SA Keys — visible for developer, admin, root */}
      {canGenerateSAKey && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <Key size={16} />
                  Service Account Key
                </CardTitle>
                <CardDescription className="mt-1">
                  Digunakan untuk akses otomatis antar sistem (machine-to-machine)
                </CardDescription>
              </div>
              <Button size="sm" onClick={handleGenerateKey} disabled={isGenerating}>
                <Plus size={15} className="mr-1" />
                {isGenerating ? 'Membuat...' : 'Buat Key Baru'}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-0 space-y-4">
            {/* New key display */}
            {newKey && (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="flex items-start gap-2 mb-3">
                  <AlertCircle size={16} className="text-amber-600 shrink-0 mt-0.5" />
                  <p className="text-sm text-amber-800 font-medium">
                    Simpan private key ini sekarang — tidak akan ditampilkan lagi!
                  </p>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between bg-white rounded border px-3 py-2">
                    <div>
                      <span className="text-xs text-muted-foreground block">Client ID</span>
                      <code className="text-slate-800">{newKey.client_id}</code>
                    </div>
                  </div>
                  <div className="flex items-center justify-between bg-white rounded border px-3 py-2">
                    <div className="flex-1 min-w-0 mr-2">
                      <span className="text-xs text-muted-foreground block">Private Key</span>
                      <code className="text-slate-800 text-xs break-all">{newKey.private_key}</code>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="shrink-0 h-8 w-8"
                      onClick={() => copyToClipboard(newKey.private_key)}
                    >
                      {copied ? (
                        <CheckCircle2 size={15} className="text-emerald-500" />
                      ) : (
                        <Copy size={15} />
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Existing keys table */}
            {saData?.sakeys && saData.sakeys.length > 0 ? (
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
                      <TableCell>
                        <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">{key.client_id}</code>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">{formatDate(key.generated_at)}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{formatDate(key.expire_at)}</TableCell>
                      <TableCell>
                        <Badge variant={key.is_active ? 'success' : 'secondary'}>
                          {key.is_active ? 'Aktif' : 'Nonaktif'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">
                Belum ada service account key.
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
