import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { message, role, testType = 'default', disableTools = false, files = [] } = body;

    // Get backend URL from environment or use default
    const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:5000/api';
    const alternativeUrl = backendUrl.replace('localhost', '127.0.0.1');
    
    console.log(`Sending request to backend with role: ${role}, testType: ${testType}`);
    console.log(`Backend URL: ${backendUrl}, will try alternative: ${alternativeUrl} if needed`);
    
    // Try direct health check first
    try {
      console.log('Testing backend health API...');
      const healthResponse = await fetch(`${backendUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      });
      
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        console.log('Health check successful:', healthData);
      } else {
        console.error('Health check failed:', healthResponse.status);
      }
    } catch (healthError) {
      console.error('Health check error:', healthError);
    }
    
    try {
      // Try the main backend URL first
      try {
        console.log(`Attempting fetch to ${backendUrl}/chat`);
        // Make the actual request to the Python backend
        const response = await fetch(`${backendUrl}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            message, 
            role, 
            testType, // Using camelCase here
            disableTools,
            files 
          }),
          // Use a longer timeout for complex queries that might generate tables
          signal: testType === 'default' ? AbortSignal.timeout(300000) : AbortSignal.timeout(120000)
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`Backend error (${response.status}):`, errorText);
          throw new Error(`Backend responded with status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Successfully received data from backend:', data);
        return NextResponse.json(data, { status: 200 });
      } catch (mainUrlError) {
        console.error('Main URL fetch error:', mainUrlError);
        console.log('Trying alternative URL...');
        
        // Try the alternative URL format (127.0.0.1 instead of localhost)
        const altResponse = await fetch(`${alternativeUrl}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            message, 
            role, 
            test_type: testType, // Using snake_case here
            disable_tools: disableTools,
            files 
          }),
          signal: testType === 'default' ? AbortSignal.timeout(300000) : AbortSignal.timeout(120000)
        });
        
        if (!altResponse.ok) {
          const errorText = await altResponse.text();
          console.error(`Alternative backend error (${altResponse.status}):`, errorText);
          throw new Error(`Alternative backend responded with status: ${altResponse.status}`);
        }
        
        const data = await altResponse.json();
        console.log('Successfully received data from alternative backend:', data);
        return NextResponse.json(data, { status: 200 });
      }
    } catch (fetchError) {
      console.error('All fetch attempts failed:', fetchError);
      
      // Instead of returning a mock response in development mode,
      // return the actual error so we can debug it
      throw fetchError;
    }
    
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to process the request', 
        details: error instanceof Error ? error.message : String(error),
        content: `[ERROR] Backend connection failed. Please check the server logs for details.`,
        timestamp: new Date().toISOString(),
      }, 
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