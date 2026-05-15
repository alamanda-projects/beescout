import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const PUBLIC_PATHS = ['/login', '/setup']

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')
  const { pathname } = request.nextUrl
  const isPublic = PUBLIC_PATHS.includes(pathname)

  if (!token && !isPublic) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  if (token && isPublic) {
    const tokenValue = token.value ?? ''
    const bare = tokenValue.replace(/^"?Bearer\s+/, '').replace(/"$/, '')
    const parts = bare.split('.')
    if (parts.length !== 3) {
      // malformed token — clear it and let user stay on login
      const res = NextResponse.next()
      res.cookies.delete('access_token')
      return res
    }
    return NextResponse.redirect(new URL('/', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)'],
}
