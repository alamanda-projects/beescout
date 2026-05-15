'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import { createRootAccount, getSetupStatus } from '@/lib/api/auth'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { CheckCircle2, Loader2, ShieldCheck, ShieldPlus } from 'lucide-react'

const schema = z.object({
  username: z.string().min(3, 'Minimal 3 karakter').max(50, 'Maksimal 50 karakter'),
  name: z.string().min(1, 'Nama wajib diisi'),
  password: z.string().min(8, 'Minimal 8 karakter')
    .regex(/[A-Z]/, 'Harus ada huruf besar')
    .regex(/[a-z]/, 'Harus ada huruf kecil')
    .regex(/[0-9]/, 'Harus ada angka')
    .regex(/[^A-Za-z0-9]/, 'Harus ada karakter khusus'),
  confirmPassword: z.string().min(1, 'Konfirmasi password wajib diisi'),
  data_domain: z.string().min(1, 'Domain data wajib diisi'),
  import_sample_contracts: z.boolean(),
  import_catalog_rules: z.boolean(),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Konfirmasi password tidak sama',
  path: ['confirmPassword'],
})

type FormData = z.infer<typeof schema>

function extractError(err: unknown) {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((item) => {
    if (item && typeof item === 'object' && 'msg' in item) return String(item.msg)
    return JSON.stringify(item)
  }).join('; ')
  return 'Setup awal gagal.'
}

export default function SetupPage() {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [created, setCreated] = useState(false)
  const { data: setupStatus, isLoading, refetch } = useQuery({
    queryKey: ['setup-status'],
    queryFn: getSetupStatus,
    retry: 1,
  })

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      username: 'superadmin',
      name: 'Super Administrator',
      data_domain: 'all',
      import_sample_contracts: false,
      import_catalog_rules: true,
    },
  })

  useEffect(() => {
    if (setupStatus?.setup_complete && !created) {
      router.replace('/login')
    }
  }, [created, router, setupStatus?.setup_complete])

  const onSubmit = async (data: FormData) => {
    setIsSubmitting(true)
    try {
      await createRootAccount({
        username: data.username,
        password: data.password,
        name: data.name,
        data_domain: data.data_domain,
        import_sample_contracts: data.import_sample_contracts,
        import_catalog_rules: data.import_catalog_rules,
      })
      setCreated(true)
      toast.success('Super Admin berhasil dibuat.')
      await refetch()
      router.push('/login')
    } catch (err) {
      toast.error(extractError(err))
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <Loader2 className="h-6 w-6 animate-spin text-amber-400" />
      </div>
    )
  }

  if (setupStatus?.setup_complete && created) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <Card className="w-full max-w-md border-slate-700 bg-slate-900 text-white">
          <CardHeader>
            <CheckCircle2 className="mb-2 h-9 w-9 text-emerald-400" />
            <CardTitle>Setup selesai</CardTitle>
            <CardDescription className="text-slate-400">Silakan login dengan akun Super Admin yang baru dibuat.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button className="w-full bg-amber-500 text-slate-950 hover:bg-amber-600" onClick={() => router.push('/login')}>
              Ke halaman login
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-10 text-white">
      <div className="mx-auto w-full max-w-md">
        <div className="mb-7 text-center">
          <div className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-lg bg-amber-500/10">
            <ShieldPlus className="h-8 w-8 text-amber-400" />
          </div>
          <h1 className="text-2xl font-bold">Setup Awal BeeScout</h1>
          <p className="mt-1 text-sm text-slate-400">Buat akun Super Admin pertama dan pilih kondisi awal database.</p>
        </div>

        <Card className="border-slate-700 bg-slate-900 text-white shadow-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ShieldCheck className="h-5 w-5 text-amber-400" />
              Super Admin
            </CardTitle>
            <CardDescription className="text-slate-400">Setup ini hanya bisa dipakai satu kali selama belum ada akun root aktif.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
              <div className="space-y-1.5">
                <Label htmlFor="username" className="text-slate-300">Username</Label>
                <Input id="username" autoComplete="username" className="border-slate-700 bg-slate-800 text-white" {...register('username')} />
                {errors.username && <p className="text-xs text-red-400">{errors.username.message}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="name" className="text-slate-300">Nama</Label>
                <Input id="name" autoComplete="name" className="border-slate-700 bg-slate-800 text-white" {...register('name')} />
                {errors.name && <p className="text-xs text-red-400">{errors.name.message}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="data_domain" className="text-slate-300">Domain Data</Label>
                <Input id="data_domain" className="border-slate-700 bg-slate-800 text-white" {...register('data_domain')} />
                {errors.data_domain && <p className="text-xs text-red-400">{errors.data_domain.message}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="password" className="text-slate-300">Password</Label>
                <Input id="password" type="password" autoComplete="new-password" className="border-slate-700 bg-slate-800 text-white" {...register('password')} />
                {errors.password && <p className="text-xs text-red-400">{errors.password.message}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="confirmPassword" className="text-slate-300">Konfirmasi Password</Label>
                <Input id="confirmPassword" type="password" autoComplete="new-password" className="border-slate-700 bg-slate-800 text-white" {...register('confirmPassword')} />
                {errors.confirmPassword && <p className="text-xs text-red-400">{errors.confirmPassword.message}</p>}
              </div>

              <div className="flex items-start gap-3 rounded-lg border border-slate-700 bg-slate-800/70 p-3">
                <Checkbox
                  id="import_sample_contracts"
                  checked={watch('import_sample_contracts')}
                  onCheckedChange={(checked) => setValue('import_sample_contracts', checked === true)}
                  className="mt-0.5 border-slate-500 data-[state=checked]:bg-amber-500 data-[state=checked]:text-slate-950"
                />
                <div className="space-y-1">
                  <Label htmlFor="import_sample_contracts" className="text-sm font-medium text-slate-200">
                    Import contoh data contract
                  </Label>
                  <p className="text-xs leading-relaxed text-slate-400">
                    Biarkan tidak dicentang untuk memulai dengan database kontrak kosong.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 rounded-lg border border-slate-700 bg-slate-800/70 p-3">
                <Checkbox
                  id="import_catalog_rules"
                  checked={watch('import_catalog_rules')}
                  onCheckedChange={(checked) => setValue('import_catalog_rules', checked === true)}
                  className="mt-0.5 border-slate-500 data-[state=checked]:bg-amber-500 data-[state=checked]:text-slate-950"
                />
                <div className="space-y-1">
                  <Label htmlFor="import_catalog_rules" className="text-sm font-medium text-slate-200">
                    Import add-on katalog aturan kualitas bawaan
                  </Label>
                  <p className="text-xs leading-relaxed text-slate-400">
                    Disarankan aktif agar form kualitas data langsung punya modul aturan siap pakai.
                  </p>
                </div>
              </div>

              <Button type="submit" className="w-full bg-amber-500 font-semibold text-slate-950 hover:bg-amber-600" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isSubmitting ? 'Membuat akun...' : 'Buat Super Admin'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
