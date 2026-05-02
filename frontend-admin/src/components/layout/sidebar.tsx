'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { LayoutDashboard, FileText, Users, User, FilePlus, Puzzle, ClipboardCheck } from 'lucide-react'
import { cn } from '@/lib/utils'
import { getPendingApprovals } from '@/lib/api/admin'

const navItems = [
  { href: '/',             label: 'Dashboard',       icon: LayoutDashboard },
  { href: '/contracts',    label: 'Data Contract',   icon: FileText },
  { href: '/catalog',      label: 'Katalog Aturan',  icon: Puzzle },
  { href: '/contracts/new', label: 'Tambah Kontrak', icon: FilePlus, indent: true },
  { href: '/approvals',    label: 'Persetujuan',     icon: ClipboardCheck, badge: true },
  { href: '/users',        label: 'Manajemen User',  icon: Users },
  { href: '/profile',      label: 'Profil Saya',     icon: User },
]

export function Sidebar() {
  const pathname = usePathname()
  const { data: pendingApprovals = [] } = useQuery({
    queryKey: ['pending-approvals'],
    queryFn: getPendingApprovals,
    refetchInterval: 60_000,
  })

  return (
    <aside className="w-60 bg-slate-900 text-white flex flex-col h-full shrink-0">
      {/* Brand */}
      <div className="px-6 py-5 border-b border-slate-700/60">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🐝</span>
          <div>
            <h1 className="text-base font-bold leading-tight">BeeScout</h1>
            <p className="text-amber-400 text-xs font-medium">Panel Admin</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navItems.map(({ href, label, icon: Icon, indent, badge }) => {
          const isActive = href === '/' ? pathname === '/' : pathname === href || pathname.startsWith(href + '/')
          const isNew = href === '/contracts/new'
          const pendingCount = badge ? pendingApprovals.length : 0

          if (isNew) {
            return (
              <Link key={href} href={href}
                className={cn(
                  'flex items-center gap-2.5 ml-4 px-3 py-2 rounded-lg text-xs font-medium transition-colors',
                  isActive
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'
                )}>
                <Icon size={14} />
                {label}
              </Link>
            )
          }

          return (
            <Link key={href} href={href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )}>
              <Icon size={17} />
              <span className="flex-1">{label}</span>
              {pendingCount > 0 && (
                <span className="bg-amber-500 text-white text-xs font-bold rounded-full px-1.5 py-0.5 min-w-[20px] text-center leading-none">
                  {pendingCount}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      <div className="px-6 py-4 border-t border-slate-700/60">
        <p className="text-slate-500 text-xs">Admin Portal · v0.1.0</p>
      </div>
    </aside>
  )
}
