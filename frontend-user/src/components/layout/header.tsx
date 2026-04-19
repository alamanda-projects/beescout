'use client'

import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { getMe, logout } from '@/lib/api/auth'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ChevronDown, LogOut, User } from 'lucide-react'
import { ROLE_LABELS } from '@/types/user'
import { toast } from 'sonner'

export function Header() {
  const router = useRouter()

  const { data: user } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    staleTime: 5 * 60 * 1000,
  })

  const handleLogout = async () => {
    try {
      await logout()
      router.push('/login')
      router.refresh()
    } catch {
      toast.error('Gagal keluar. Coba lagi.')
    }
  }

  const initials = user?.client_id?.charAt(0)?.toUpperCase() ?? 'U'
  const roleLabel = user?.group_access ? ROLE_LABELS[user.group_access] : ''

  return (
    <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 shrink-0">
      <div />

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="flex items-center gap-2 h-9 px-2">
            <Avatar className="h-7 w-7">
              <AvatarFallback className="bg-indigo-100 text-indigo-700 text-xs font-semibold">
                {initials}
              </AvatarFallback>
            </Avatar>
            <div className="text-left hidden sm:block">
              <p className="text-sm font-medium leading-none">{user?.client_id ?? '...'}</p>
              {roleLabel && (
                <p className="text-xs text-muted-foreground mt-0.5">{roleLabel}</p>
              )}
            </div>
            <ChevronDown size={15} className="text-muted-foreground" />
          </Button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuLabel>
            <p className="font-medium">{user?.client_id}</p>
            <p className="text-xs text-muted-foreground font-normal">{user?.data_domain}</p>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => router.push('/profile')}>
            <User className="mr-2 h-4 w-4" />
            Profil Saya
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleLogout} className="text-red-600 focus:text-red-600">
            <LogOut className="mr-2 h-4 w-4" />
            Keluar
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  )
}
