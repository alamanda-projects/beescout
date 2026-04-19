'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { getMe, logout } from '@/lib/api/auth'
import { Sidebar } from '@/components/layout/sidebar'
import { Header } from '@/components/layout/header'
import { Skeleton } from '@/components/ui/skeleton'
import { ShieldX } from 'lucide-react'

const ADMIN_ROLES = ['admin', 'root']

export default function AdminProtectedLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { data: user, isLoading, isError } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    retry: 1,
  })

  useEffect(() => {
    if (isLoading) return
    if (isError) {
      logout().catch(() => {}).finally(() => router.replace('/login'))
      return
    }
    if (user && !ADMIN_ROLES.includes(user.group_access)) {
      logout().catch(() => {}).finally(() => router.replace('/login?error=forbidden'))
    }
  }, [user, isLoading, isError, router])

  if (isLoading || (!user && !isError)) {
    return (
      <div className="flex h-screen bg-slate-50 overflow-hidden">
        <div className="w-60 bg-slate-900 shrink-0" />
        <div className="flex flex-col flex-1 p-8 gap-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    )
  }

  if (isError || !user || !ADMIN_ROLES.includes(user.group_access)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <ShieldX size={48} className="mx-auto text-red-400 mb-4" />
          <h2 className="text-lg font-semibold text-slate-800">Akses Ditolak</h2>
          <p className="text-sm text-muted-foreground mt-1">Halaman ini hanya untuk admin dan root.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  )
}
