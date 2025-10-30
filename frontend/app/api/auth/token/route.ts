import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // For now, return a placeholder token
    // In production, this would get the actual Auth0 access token
    return NextResponse.json({ 
      accessToken: 'placeholder-token-for-development',
      message: 'Access token endpoint - production implementation needed'
    });
  } catch (error) {
    console.error('Error getting access token:', error);
    return NextResponse.json(
      { error: 'Failed to get access token' },
      { status: 500 }
    );
  }
}
