import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { message, role, testType = 'default', disableTools = false, files = [] } = body;

    // Get backend URL from environment or use default
    const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:5000/api';
    
    console.log(`Sending request to backend with role: ${role}, testType: ${testType}`);
    
    try {
      // Make the actual request to the Python backend
      const response = await fetch(`${backendUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message, 
          role, 
          test_type: testType,
          disable_tools: disableTools,
          files 
        }),
        // Use a longer timeout for Excel processing
        signal: AbortSignal.timeout(60000)
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Backend error (${response.status}):`, errorText);
        throw new Error(`Backend responded with status: ${response.status}`);
      }
      
      const data = await response.json();
      return NextResponse.json(data, { status: 200 });
    } catch (fetchError) {
      console.error('Fetch error:', fetchError);
      
      // If we're in development mode, return a mock response
      if (process.env.NODE_ENV === 'development') {
        console.log('Returning mock response in development mode');
        return NextResponse.json({
          content: `[DEV MODE] This is a simulated response. Would have sent: ${message} to ${role} agent with test type ${testType}.`,
          timestamp: new Date().toISOString(),
        }, { status: 200 });
      }
      
      throw fetchError;
    }
    
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { error: 'Failed to process the request', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}

// API route to handle file uploads
export async function PUT(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get('file') as File;
    
    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }
    
    const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:5000/api';
    
    // Create a new FormData instance to forward the file
    const forwardFormData = new FormData();
    forwardFormData.append('file', file);
    
    // Forward the file to the Python backend
    const response = await fetch(`${backendUrl}/upload`, {
      method: 'POST',
      body: forwardFormData,
    });
    
    if (!response.ok) {
      throw new Error(`File upload failed with status: ${response.status}`);
    }
    
    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
    
  } catch (error) {
    console.error('File upload error:', error);
    return NextResponse.json(
      { error: 'Failed to upload file', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
} 