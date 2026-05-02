import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const PUBLIC_PATHS = ['/login']

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')
  const { pathname } = request.nextUrl
  const isPublic = PUBLIC_PATHS.includes(pathname)

  // No token → redirect to login (except on public pages)
  if (!token && !isPublic) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Has token + on login page → validate format first
  if (token && isPublic) {
    const tokenValue = token.value ?? ''
    const bare = tokenValue.replace(/^"?Bearer\s+/, '').replace(/"$/, '')
    const parts = bare.split('.')
    if (parts.length !== 3) {
      const res = NextResponse.next()
      res.cookies.delete('access_token')
      return res
    }
    return NextResponse.redirect(new URL('/', request.url))
  }

  return NextResponse.next()
}

export const config = {
  // Match all routes except Next.js internals and static assets
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)'],
}
