import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest, { params }: { params: { auth0: string[] } }) {
  const route = params.auth0?.[0];
  const { searchParams } = new URL(request.url);
  
  try {
    switch (route) {
      case 'login':
        // Redirect to Auth0 login
        const loginUrl = `https://${process.env.AUTH0_DOMAIN}/authorize?` +
          `client_id=${process.env.AUTH0_CLIENT_ID}&` +
          `response_type=code&` +
          `redirect_uri=${process.env.AUTH0_BASE_URL}/api/auth/callback&` +
          `scope=${encodeURIComponent('openid profile email')}&` +
          `audience=${process.env.AUTH0_AUDIENCE}`;
        return NextResponse.redirect(loginUrl);
        
      case 'logout':
        // Redirect to Auth0 logout
        const logoutUrl = `https://${process.env.AUTH0_DOMAIN}/v2/logout?` +
          `client_id=${process.env.AUTH0_CLIENT_ID}&` +
          `returnTo=${process.env.AUTH0_BASE_URL}`;
        return NextResponse.redirect(logoutUrl);
        
      case 'callback':
        // Handle Auth0 callback
        const code = searchParams.get('code');
        if (code) {
          // In a real implementation, you'd exchange the code for tokens
          // For now, redirect to dashboard
          return NextResponse.redirect(new URL('/dashboard', request.url));
        }
        return NextResponse.redirect(new URL('/?error=auth_failed', request.url));
        
      case 'me':
        // Return user info
        return NextResponse.json({ user: null }); // Placeholder
        
      default:
        return NextResponse.json({ error: 'Auth route not found' }, { status: 404 });
    }
  } catch (error) {
    console.error('Auth error:', error);
    return NextResponse.json({ error: 'Authentication failed' }, { status: 500 });
  }
}
