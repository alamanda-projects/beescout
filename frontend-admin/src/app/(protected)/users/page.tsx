'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import { getMe } from '@/lib/api/auth'
import { createUser } from '@/lib/api/admin'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { toast } from 'sonner'
import { Loader2, UserPlus, Info, CheckCircle2 } from 'lucide-react'

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

export default function UsersPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const { data: currentUser } = useQuery({ queryKey: ['me'], queryFn: getMe })
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
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      if (msg?.includes('403') || (err as { response?: { status?: number } })?.response?.status === 403) {
        toast.error('Hanya Super Admin (root) yang dapat membuat user baru.')
      } else {
        toast.error(msg || 'Gagal membuat user.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Manajemen User</h2>
        <p className="text-sm text-muted-foreground mt-1">Buat akun baru untuk anggota tim</p>
      </div>

      {!isRoot && (
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <Info size={16} className="text-amber-600 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-amber-800">Akses Terbatas</p>
            <p className="text-sm text-amber-700 mt-0.5">
              Hanya akun <Badge variant="warning" className="text-xs mx-0.5">Super Admin</Badge> yang dapat membuat user baru.
              Akun Anda saat ini: <Badge variant="secondary" className="text-xs">{currentUser?.group_access}</Badge>
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
          <CardDescription>
            Akun baru akan langsung bisa digunakan setelah disimpan
          </CardDescription>
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

      <Card className="border-slate-200 bg-slate-50">
        <CardContent className="pt-5">
          <p className="text-xs font-medium text-slate-700 mb-2">Catatan Peran & Hak Akses</p>
          <div className="space-y-1.5 text-xs text-muted-foreground">
            <div className="flex gap-2"><Badge variant="outline" className="text-xs w-20 justify-center">user</Badge><span>Dapat melihat kontrak sesuai domain yang ditentukan</span></div>
            <div className="flex gap-2"><Badge variant="outline" className="text-xs w-20 justify-center">developer</Badge><span>Akses baca lebih luas + generate service account key</span></div>
            <div className="flex gap-2"><Badge variant="warning" className="text-xs w-20 justify-center">admin</Badge><span>Kelola kontrak + akses panel admin</span></div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
