'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getMe } from '@/lib/api/auth'
import { createUser, getUsers } from '@/lib/api/admin'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { Loader2, UserPlus, Info, CheckCircle2, Users, Search } from 'lucide-react'

const schema = z.object({
  username: z.string().min(3, 'Minimal 3 karakter').max(50),
  password: z.string().min(8, 'Minimal 8 karakter')
    .regex(/[A-Z]/, 'Harus ada huruf besar')
    .regex(/[a-z]/, 'Harus ada huruf kecil')
    .regex(/[0-9]/, 'Harus ada angka')
    .regex(/[^A-Za-z0-9]/, 'Harus ada karakter khusus'),
  name: z.string().min(1, 'Nama wajib diisi'),
  group_access: z.string().min(1, 'Pilih peran'),
  data_domain: z.string().min(1, 'Domain wajib diisi'),
  is_active: z.boolean(),
})

type FormData = z.infer<typeof schema>

const ROLE_BADGE: Record<string, string> = {
  root:      'bg-red-100 text-red-700 border-red-200',
  admin:     'bg-amber-100 text-amber-700 border-amber-200',
  developer: 'bg-blue-100 text-blue-700 border-blue-200',
  user:      'bg-slate-100 text-slate-600 border-slate-200',
}

export default function UsersPage() {
  const queryClient = useQueryClient()
  const [isLoading, setIsLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [search, setSearch] = useState('')

  const { data: currentUser } = useQuery({ queryKey: ['me'], queryFn: getMe })
  const { data: users = [], isLoading: usersLoading } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
  })

  const isRoot = currentUser?.group_access === 'root'

  const { register, handleSubmit, reset, setValue, formState: { errors }, watch } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { is_active: true, group_access: '' },
  })

  const onSubmit = async (data: FormData) => {
    setIsLoading(true)
    setSuccess(false)
    try {
      await createUser(data)
      toast.success(`User "${data.username}" berhasil dibuat!`)
      setSuccess(true)
      reset()
      queryClient.invalidateQueries({ queryKey: ['users'] })
    } catch (err: unknown) {
      const detail = (err as any)?.response?.data?.detail
      let msg = 'Gagal membuat user.'
      if (typeof detail === 'string') msg = detail
      else if (Array.isArray(detail)) msg = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
      toast.error(msg)
    } finally {
      setIsLoading(false)
    }
  }

  const filtered = users.filter(u => {
    const q = search.toLowerCase()
    return !q ||
      u.username.toLowerCase().includes(q) ||
      u.name.toLowerCase().includes(q) ||
      u.group_access.toLowerCase().includes(q) ||
      u.data_domain.toLowerCase().includes(q)
  })

  const activeCount   = users.filter(u => u.is_active).length
  const inactiveCount = users.filter(u => !u.is_active).length

  return (
    <div className="space-y-5 max-w-4xl">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Manajemen User</h2>
        <p className="text-sm text-muted-foreground mt-1">Lihat daftar user dan buat akun baru</p>
      </div>

      <Tabs defaultValue="list">
        <TabsList className="grid w-full grid-cols-2 max-w-sm">
          <TabsTrigger value="list" className="flex items-center gap-1.5">
            <Users size={14} />Daftar User
          </TabsTrigger>
          <TabsTrigger value="create" className="flex items-center gap-1.5">
            <UserPlus size={14} />Buat User Baru
          </TabsTrigger>
        </TabsList>

        {/* ── Tab: Daftar User ─────────────────────────────────────── */}
        <TabsContent value="list" className="mt-4 space-y-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Cari username, nama, domain..."
                className="pl-8 h-9"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-3 text-sm text-muted-foreground ml-auto">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                {activeCount} aktif
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-slate-300 inline-block" />
                {inactiveCount} nonaktif
              </span>
            </div>
          </div>

          <Card>
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead className="w-[160px]">Username</TableHead>
                  <TableHead>Nama</TableHead>
                  <TableHead className="w-[110px]">Peran</TableHead>
                  <TableHead>Domain</TableHead>
                  <TableHead className="w-[90px] text-center">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {usersLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 5 }).map((_, j) => (
                        <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-10 text-muted-foreground text-sm">
                      {search ? 'Tidak ada user yang cocok dengan pencarian.' : 'Belum ada user terdaftar.'}
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map(u => (
                    <TableRow key={u.username} className={!u.is_active ? 'opacity-50' : ''}>
                      <TableCell className="font-mono text-xs font-medium">{u.username}</TableCell>
                      <TableCell className="text-sm">{u.name}</TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${ROLE_BADGE[u.group_access] ?? ROLE_BADGE.user}`}>
                          {u.group_access}
                        </span>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">{u.data_domain}</TableCell>
                      <TableCell className="text-center">
                        {u.is_active ? (
                          <span className="inline-flex items-center gap-1 text-xs text-emerald-600">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />Aktif
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs text-slate-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />Nonaktif
                          </span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>

          <Card className="border-slate-200 bg-slate-50">
            <CardContent className="pt-4 pb-4">
              <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                {Object.entries(ROLE_BADGE).filter(([k]) => k !== 'root').map(([role, cls]) => (
                  <div key={role} className="flex items-center gap-1.5">
                    <span className={`px-1.5 py-0.5 rounded border text-xs font-medium ${cls}`}>{role}</span>
                    <span>{{ user: 'Lihat kontrak (domain sendiri)', developer: 'Lihat kontrak luas + SA key', admin: 'Kelola kontrak + user' }[role]}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Tab: Buat User Baru ──────────────────────────────────── */}
        <TabsContent value="create" className="mt-4 space-y-4 max-w-2xl">
          {!isRoot && (
            <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <Info size={16} className="text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-amber-800">Akses Terbatas</p>
                <p className="text-sm text-amber-700 mt-0.5">
                  Hanya akun <Badge variant="outline" className="text-xs mx-0.5">Super Admin</Badge> yang dapat membuat user baru.
                  Akun Anda: <Badge variant="secondary" className="text-xs">{currentUser?.group_access}</Badge>
                </p>
              </div>
            </div>
          )}

          {success && (
            <div className="flex items-center gap-3 p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
              <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
              <p className="text-sm text-emerald-800">User berhasil dibuat. Sampaikan kredensial kepada pengguna secara aman.</p>
            </div>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <UserPlus size={16} /> Buat User Baru
              </CardTitle>
              <CardDescription>Akun baru langsung bisa digunakan setelah disimpan</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label>Username *</Label>
                    <Input placeholder="username_unik" {...register('username')} />
                    {errors.username && <p className="text-xs text-destructive">{errors.username.message}</p>}
                  </div>
                  <div className="space-y-1.5">
                    <Label>Nama Lengkap *</Label>
                    <Input placeholder="Nama Pengguna" {...register('name')} />
                    {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label>Password *</Label>
                  <Input type="password" placeholder="Min. 8 karakter, huruf besar, angka, simbol"
                    {...register('password')} />
                  {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
                  <p className="text-xs text-muted-foreground">
                    Contoh kuat: <code className="bg-slate-100 px-1 rounded">Admin@1234</code>
                  </p>
                </div>

                <Separator />

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label>Peran *</Label>
                    <Select onValueChange={(v) => setValue('group_access', v)}>
                      <SelectTrigger><SelectValue placeholder="Pilih peran" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="user">Pengguna (user)</SelectItem>
                        <SelectItem value="developer">Developer</SelectItem>
                        <SelectItem value="admin">Admin</SelectItem>
                      </SelectContent>
                    </Select>
                    {errors.group_access && <p className="text-xs text-destructive">{errors.group_access.message}</p>}
                  </div>
                  <div className="space-y-1.5">
                    <Label>Domain Data *</Label>
                    <Input placeholder="Contoh: penjualan, inventory" {...register('data_domain')} />
                    {errors.data_domain && <p className="text-xs text-destructive">{errors.data_domain.message}</p>}
                  </div>
                </div>

                <div className="flex items-center gap-2 p-3 bg-slate-50 rounded-lg">
                  <input
                    type="checkbox"
                    id="is_active"
                    className="rounded"
                    checked={watch('is_active')}
                    onChange={(e) => setValue('is_active', e.target.checked)}
                  />
                  <Label htmlFor="is_active" className="cursor-pointer font-normal">
                    Akun langsung aktif setelah dibuat
                  </Label>
                </div>

                <Button type="submit" className="w-full" disabled={isLoading || !isRoot}>
                  {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isLoading ? 'Membuat...' : 'Buat User'}
                </Button>

                {!isRoot && (
                  <p className="text-xs text-center text-muted-foreground">
                    Tombol dinonaktifkan — Anda bukan Super Admin
                  </p>
                )}
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
