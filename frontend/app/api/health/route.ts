import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Basic health check - no Auth0 dependency
    return NextResponse.json(
      {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        service: 'speech-coach-frontend',
        version: '1.0.0'
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: 'Health check failed'
      },
      { status: 500 }
    );
  }
}