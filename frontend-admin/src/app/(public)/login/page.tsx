'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { login } from '@/lib/api/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from 'sonner'
import { Loader2, ShieldCheck } from 'lucide-react'

const schema = z.object({
  username: z.string().min(1, 'Username wajib diisi'),
  password: z.string().min(1, 'Password wajib diisi'),
})
type FormData = z.infer<typeof schema>

export default function LoginPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({ resolver: zodResolver(schema) })

  const onSubmit = async (data: FormData) => {
    setIsLoading(true)
    try {
      await login(data.username, data.password)
      router.push('/')
      router.refresh()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Login gagal.'
      toast.error(msg)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-amber-500/10 rounded-2xl mb-4">
            <ShieldCheck size={32} className="text-amber-400" />
          </div>
          <h1 className="text-2xl font-bold text-white">BeeScout Admin</h1>
          <p className="text-slate-400 text-sm mt-1">Portal Administrasi — Akses Terbatas</p>
        </div>

        <Card className="border-slate-700 bg-slate-800 text-white shadow-xl">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg text-white">Masuk</CardTitle>
            <CardDescription className="text-slate-400">Hanya untuk akun admin dan root</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="username" className="text-slate-300">Username</Label>
                <Input id="username" placeholder="username" autoComplete="username" autoFocus
                  className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                  {...register('username')} />
                {errors.username && <p className="text-xs text-red-400">{errors.username.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password" className="text-slate-300">Password</Label>
                <Input id="password" type="password" placeholder="••••••••" autoComplete="current-password"
                  className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                  {...register('password')} />
                {errors.password && <p className="text-xs text-red-400">{errors.password.message}</p>}
              </div>
              <Button type="submit" className="w-full bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold" disabled={isLoading}>
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isLoading ? 'Memproses...' : 'Masuk'}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-slate-600 mt-6">
          Akses tidak sah akan dilaporkan dan dicatat.
        </p>
      </div>
    </div>
  )
}
