import { NextRequest, NextResponse } from "next/server";

// Environment variables
const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://hackradar.onrender.com/api";

/**
 * POST handler for notification subscriptions
 * This acts as a proxy to avoid CORS issues with the backend
 */
export async function POST(request: NextRequest) {
  try {
    // Parse the request body
    const body = await request.json();
    
    // Forward the request to the backend
    const response = await fetch(`${API_URL}/notifications/subscribe`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    // If the backend request failed
    if (!response.ok) {
      console.error(`Backend returned ${response.status}: ${response.statusText}`);
      return NextResponse.json(
        { error: 'Error subscribing to topic', status: response.status },
        { status: response.status }
      );
    }
    
    // Return the backend response
    const data = await response.json();
    return NextResponse.json(data);
    
  } catch (error) {
    console.error('Error in notifications subscribe API route:', error);
    return NextResponse.json(
      { error: 'Internal server error' }, 
      { status: 500 }
    );
  }
} 