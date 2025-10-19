import { NextRequest, NextResponse } from 'next/server';

// Simple auth handlers for development
export async function GET(request: NextRequest, { params }: { params: { auth0: string[] } }) {
  const route = params.auth0?.[0];
  
  switch (route) {
    // case 'login':
    //   // For development, just redirect to dashboard
    //   return NextResponse.redirect(new URL('/dashboard', request.url));
    
    case 'logout':
      // For development, just redirect to home
      return NextResponse.redirect(new URL('/', request.url));
    
    case 'callback':
      // For development, redirect to dashboard
      return NextResponse.redirect(new URL('/dashboard', request.url));
    
    default:
      return NextResponse.json({ error: 'Auth route not found' }, { status: 404 });
  }
}

export async function POST(request: NextRequest) {
  return NextResponse.json({ error: 'POST not supported in development mode' }, { status: 405 });
}
