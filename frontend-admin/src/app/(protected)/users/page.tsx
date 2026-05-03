'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { getMe } from '@/lib/api/auth'
import { createUser, getUsers, updateUser, deleteUser } from '@/lib/api/admin'
import type { UserRecord } from '@/lib/api/admin'
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
import { Loader2, UserPlus, Info, CheckCircle2, Users, Search, Pencil, Trash2, X, Save, ShieldOff, ShieldCheck } from 'lucide-react'

// ─── Schema ───────────────────────────────────────────────────────────────────
const createSchema = z.object({
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

const editSchema = z.object({
  name: z.string().min(1, 'Nama wajib diisi'),
  group_access: z.string().min(1, 'Pilih peran'),
  data_domain: z.string().min(1, 'Domain wajib diisi'),
  password: z.string().optional(),
})

type CreateFormData = z.infer<typeof createSchema>
type EditFormData = z.infer<typeof editSchema>

const ROLE_BADGE: Record<string, string> = {
  root:      'bg-red-100 text-red-700 border-red-200',
  admin:     'bg-amber-100 text-amber-700 border-amber-200',
  developer: 'bg-blue-100 text-blue-700 border-blue-200',
  user:      'bg-slate-100 text-slate-600 border-slate-200',
}

// ─── Edit Panel ───────────────────────────────────────────────────────────────
function EditPanel({
  user,
  onClose,
  onSaved,
}: {
  user: UserRecord
  onClose: () => void
  onSaved: () => void
}) {
  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      name: user.name,
      group_access: user.group_access,
      data_domain: user.data_domain,
      password: '',
    },
  })

  const { mutate, isPending } = useMutation({
    mutationFn: (data: EditFormData) => {
      const payload: Record<string, unknown> = {
        name: data.name,
        group_access: data.group_access,
        data_domain: data.data_domain,
      }
      if (data.password?.trim()) payload.password = data.password
      return updateUser(user.username, payload)
    },
    onSuccess: () => {
      toast.success(`User "${user.username}" berhasil diperbarui.`)
      onSaved()
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail
      let msg = 'Gagal memperbarui user.'
      if (typeof detail === 'string') msg = detail
      else if (Array.isArray(detail)) msg = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
      toast.error(msg)
    },
  })

  return (
    <tr>
      <td colSpan={6} className="p-0">
        <div className="bg-indigo-50 border-y border-indigo-100 px-4 py-4">
          <form onSubmit={handleSubmit((d) => mutate(d))} className="space-y-3">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-semibold text-indigo-700">Edit User: <span className="font-mono">{user.username}</span></p>
              <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-600">
                <X size={15} />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div className="space-y-1">
                <Label className="text-xs">Nama Lengkap *</Label>
                <Input className="h-8 text-xs" {...register('name')} />
                {errors.name && <p className="text-[10px] text-destructive">{errors.name.message}</p>}
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Peran *</Label>
                <Select value={watch('group_access')} onValueChange={(v) => setValue('group_access', v)}>
                  <SelectTrigger className="h-8 text-xs"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="user">user</SelectItem>
                    <SelectItem value="developer">developer</SelectItem>
                    <SelectItem value="admin">admin</SelectItem>
                  </SelectContent>
                </Select>
                {errors.group_access && <p className="text-[10px] text-destructive">{errors.group_access.message}</p>}
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Domain Data *</Label>
                <Input className="h-8 text-xs" {...register('data_domain')} />
                {errors.data_domain && <p className="text-[10px] text-destructive">{errors.data_domain.message}</p>}
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Password Baru <span className="text-muted-foreground">(opsional)</span></Label>
                <Input type="password" className="h-8 text-xs" placeholder="Kosongkan jika tidak diubah" {...register('password')} />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-1">
              <Button type="button" variant="outline" size="sm" onClick={onClose}>Batal</Button>
              <Button type="submit" size="sm" disabled={isPending}>
                {isPending ? <Loader2 size={13} className="animate-spin mr-1" /> : <Save size={13} className="mr-1" />}
                Simpan
              </Button>
            </div>
          </form>
        </div>
      </td>
    </tr>
  )
}

// ─── Delete Confirm Panel ─────────────────────────────────────────────────────
function DeletePanel({
  user,
  onClose,
  onDeleted,
}: {
  user: UserRecord
  onClose: () => void
  onDeleted: () => void
}) {
  const { mutate, isPending } = useMutation({
    mutationFn: () => deleteUser(user.username),
    onSuccess: () => {
      toast.success(`User "${user.username}" berhasil dihapus.`)
      onDeleted()
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail
      let msg = 'Gagal menghapus user.'
      if (typeof detail === 'string') msg = detail
      else if (Array.isArray(detail)) msg = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
      toast.error(msg)
    },
  })

  return (
    <tr>
      <td colSpan={6} className="p-0">
        <div className="bg-red-50 border-y border-red-100 px-4 py-3 flex items-center justify-between gap-4">
          <p className="text-sm text-red-800">
            Hapus user <span className="font-mono font-semibold">{user.username}</span> secara permanen? Tindakan ini tidak dapat dibatalkan.
          </p>
          <div className="flex gap-2 shrink-0">
            <Button variant="outline" size="sm" onClick={onClose}>Batal</Button>
            <Button size="sm" className="bg-red-600 hover:bg-red-700" disabled={isPending} onClick={() => mutate()}>
              {isPending ? <Loader2 size={13} className="animate-spin mr-1" /> : <Trash2 size={13} className="mr-1" />}
              Hapus
            </Button>
          </div>
        </div>
      </td>
    </tr>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function UsersPage() {
  const queryClient = useQueryClient()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [search, setSearch] = useState('')
  const [editTarget, setEditTarget] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)

  const { data: currentUser } = useQuery({ queryKey: ['me'], queryFn: getMe })
  const { data: users = [], isLoading: usersLoading } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
  })

  const isRoot = currentUser?.group_access === 'root'

  const { mutate: toggleActive } = useMutation({
    mutationFn: ({ username, is_active }: { username: string; is_active: boolean }) =>
      updateUser(username, { is_active }),
    onSuccess: (_, vars) => {
      toast.success(`User "${vars.username}" ${vars.is_active ? 'diaktifkan' : 'dinonaktifkan'}.`)
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail
      let msg = 'Gagal mengubah status user.'
      if (typeof detail === 'string') msg = detail
      else if (Array.isArray(detail)) msg = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
      toast.error(msg)
    },
  })

  const { register, handleSubmit, reset, setValue, formState: { errors }, watch } = useForm<CreateFormData>({
    resolver: zodResolver(createSchema),
    defaultValues: { is_active: true, group_access: '' },
  })

  const onSubmit = async (data: CreateFormData) => {
    setIsSubmitting(true)
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
      setIsSubmitting(false)
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

  function handleEditClose() { setEditTarget(null) }
  function handleDeleteClose() { setDeleteTarget(null) }
  function handleSaved() { setEditTarget(null); queryClient.invalidateQueries({ queryKey: ['users'] }) }
  function handleDeleted() { setDeleteTarget(null); queryClient.invalidateQueries({ queryKey: ['users'] }) }

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

          {isRoot && (
            <div className="flex items-center gap-2 text-xs text-indigo-700 bg-indigo-50 border border-indigo-100 rounded-lg px-3 py-2">
              <Info size={13} className="shrink-0" />
              Anda login sebagai Super Admin — dapat mengedit, menonaktifkan, dan menghapus user.
            </div>
          )}

          <Card>
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead className="w-[140px]">Username</TableHead>
                  <TableHead>Nama</TableHead>
                  <TableHead className="w-[110px]">Peran</TableHead>
                  <TableHead>Domain</TableHead>
                  <TableHead className="w-[90px] text-center">Status</TableHead>
                  {isRoot && <TableHead className="w-[120px] text-center">Aksi</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {usersLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: isRoot ? 6 : 5 }).map((_, j) => (
                        <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={isRoot ? 6 : 5} className="text-center py-10 text-muted-foreground text-sm">
                      {search ? 'Tidak ada user yang cocok dengan pencarian.' : 'Belum ada user terdaftar.'}
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.flatMap(u => {
                    const isRootUser = u.group_access === 'root'
                    const rows = [
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
                        {isRoot && (
                          <TableCell>
                            {isRootUser ? (
                              <span className="text-xs text-slate-300 block text-center">—</span>
                            ) : (
                              <div className="flex items-center justify-center gap-1">
                                <button
                                  title={u.is_active ? 'Nonaktifkan' : 'Aktifkan'}
                                  onClick={() => toggleActive({ username: u.username, is_active: !u.is_active })}
                                  className="p-1.5 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors"
                                >
                                  {u.is_active ? <ShieldOff size={14} /> : <ShieldCheck size={14} />}
                                </button>
                                <button
                                  title="Edit"
                                  onClick={() => { setDeleteTarget(null); setEditTarget(editTarget === u.username ? null : u.username) }}
                                  className={`p-1.5 rounded hover:bg-slate-100 transition-colors ${editTarget === u.username ? 'text-indigo-600 bg-indigo-50' : 'text-slate-400 hover:text-slate-700'}`}
                                >
                                  <Pencil size={14} />
                                </button>
                                <button
                                  title="Hapus"
                                  onClick={() => { setEditTarget(null); setDeleteTarget(deleteTarget === u.username ? null : u.username) }}
                                  className={`p-1.5 rounded hover:bg-red-50 transition-colors ${deleteTarget === u.username ? 'text-red-600 bg-red-50' : 'text-slate-400 hover:text-red-600'}`}
                                >
                                  <Trash2 size={14} />
                                </button>
                              </div>
                            )}
                          </TableCell>
                        )}
                      </TableRow>,
                    ]

                    if (editTarget === u.username) {
                      rows.push(
                        <EditPanel key={`edit-${u.username}`} user={u} onClose={handleEditClose} onSaved={handleSaved} />
                      )
                    }
                    if (deleteTarget === u.username) {
                      rows.push(
                        <DeletePanel key={`del-${u.username}`} user={u} onClose={handleDeleteClose} onDeleted={handleDeleted} />
                      )
                    }

                    return rows
                  })
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

                <Button type="submit" className="w-full" disabled={isSubmitting || !isRoot}>
                  {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isSubmitting ? 'Membuat...' : 'Buat User'}
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
