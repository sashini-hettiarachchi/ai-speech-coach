import { getAccessToken } from '@auth0/nextjs-auth0';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const accessToken = await getAccessToken();
    console.log("Access token retrieved:", accessToken);
    
    if (!accessToken) {
      return NextResponse.json(
        { error: 'No access token available' },
        { status: 401 }
      );
    }

    return NextResponse.json({ accessToken });
  } catch (error) {
    console.error('Error getting access token:', error);

    return NextResponse.json(
      { error: 'Failed to get access token' },
      { status: 500 }
    );
  }
}
