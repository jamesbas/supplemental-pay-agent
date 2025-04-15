"use client"

import { useState, useRef, useEffect } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import Image from "next/image"
import Link from "next/link"
import { FiSend, FiUpload, FiChevronLeft, FiMoon, FiSun, FiInfo, FiSettings, FiX } from "react-icons/fi"
import { toast } from "sonner"
import { useTheme } from "next-themes"

// Utility function to convert ASCII/Markdown tables to HTML
const formatTableContent = (content: string): string => {
  // Check if the content contains a table pattern (rows with multiple | characters)
  const hasTablePattern = /^[|\-+]*\|[|\-+]*$/m.test(content);
  
  if (!hasTablePattern) {
    return content;
  }
  
  // Split the content by lines
  const lines = content.split('\n');
  let htmlContent = content;
  
  // Find table sections (groups of lines with | characters)
  let inTable = false;
  let tableContent = '';
  let formattedContent = '';
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    // Check if line is part of a table
    if (line.includes('|') && (line.trim().startsWith('|') || line.trim().endsWith('|'))) {
      if (!inTable) {
        inTable = true;
        tableContent = '<table class="formatted-table">\n<thead>\n';
      }
      
      // Skip separator lines
      if (line.replace(/[|\-+\s]/g, '') === '') {
        if (tableContent.includes('<thead>') && !tableContent.includes('</thead>')) {
          tableContent += '</thead>\n<tbody>\n';
        }
        continue;
      }
      
      // Process table row
      const cells = line.split('|').filter(cell => cell !== '');
      tableContent += '<tr>\n';
      
      cells.forEach(cell => {
        const tag = tableContent.includes('<tbody>') ? 'td' : 'th';
        tableContent += `  <${tag}>${cell.trim()}</${tag}>\n`;
      });
      
      tableContent += '</tr>\n';
    } else {
      if (inTable) {
        inTable = false;
        if (tableContent.includes('<tbody>')) {
          tableContent += '</tbody>\n';
        } else {
          tableContent += '</thead>\n';
        }
        tableContent += '</table>\n';
        formattedContent += tableContent;
      }
      formattedContent += line + '\n';
    }
  }
  
  // Close the table if we reached the end
  if (inTable) {
    if (tableContent.includes('<tbody>')) {
      tableContent += '</tbody>\n';
    } else {
      tableContent += '</thead>\n';
    }
    tableContent += '</table>\n';
    formattedContent += tableContent;
  }
  
  // Return original content if no tables were found
  return formattedContent || content;
};

// Types
interface Message {
  role: "user" | "assistant" | "system"
  content: string
  timestamp: Date
  files?: string[]
}

interface ApiResponse {
  content: string
  timestamp: string
  files?: string[]
}

// Test types
const TEST_TYPES = [
  { id: 'default', label: 'Standard Mode' },
  { id: 'excel', label: 'Excel Analysis' },
  { id: 'simple', label: 'Simple Query' }
]

export default function ChatPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const role = searchParams.get("role") || "hr"
  const { theme, setTheme } = useTheme()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [testType, setTestType] = useState<string>("default")
  const [disableTools, setDisableTools] = useState<boolean>(false)
  const [showSettings, setShowSettings] = useState<boolean>(false)
  const messageEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Welcome messages for different roles
  const welcomeMessages = {
    hr: "Welcome to the HR Team portal. I can help you retrieve and interpret DXC policy documents related to supplemental pay. What would you like to know?",
    manager: "Welcome to the People Manager portal. I can help you calculate supplemental pay and provide approval recommendations for your team members. What would you like to calculate?",
    payroll: "Welcome to the Payroll Manager portal. I can help you analyze supplemental pay data to identify trends, outliers, and ensure policy compliance. What would you like to analyze?",
    intelligent: "Welcome to the Intelligent Supplemental Pay portal. I can answer any questions you have about supplemental pay policies, calculations, and analytics. How can I assist you today?"
  }

  // Initialize chat with system message
  useEffect(() => {
    setMessages([
      {
        role: "system",
        content: "DXC Supplemental Pay AI initialized.",
        timestamp: new Date()
      },
      {
        role: "assistant",
        content: welcomeMessages[role as keyof typeof welcomeMessages],
        timestamp: new Date()
      }
    ])
  }, [role])

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Handle file upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files)
      setUploadedFiles(prev => [...prev, ...files])
      toast.info(`${files.length} file(s) selected`)
      
      // For Excel analysis, automatically set the test type
      if (files.some(file => file.name.endsWith('.xlsx') || file.name.endsWith('.xls') || file.name.endsWith('.csv'))) {
        setTestType('excel')
        toast.info("Excel files detected - switched to Excel Analysis mode")
      }
    }
  }

  // Remove a file from the uploaded files list
  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!input.trim() && uploadedFiles.length === 0) return
    
    // Add user message
    const userMessage: Message = {
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
      files: uploadedFiles.map(file => file.name)
    }
    
    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      // Upload files if there are any
      const fileIds = []
      for (const file of uploadedFiles) {
        try {
          const formData = new FormData()
          formData.append('file', file)
          
          const uploadResponse = await fetch('/api/chat', {
            method: 'PUT',
            body: formData
          })
          
          if (!uploadResponse.ok) {
            throw new Error(`Failed to upload file: ${file.name}`)
          }
          
          const { fileId } = await uploadResponse.json()
          fileIds.push(fileId)
        } catch (fileError) {
          console.error('File upload error:', fileError)
          toast.error(`Failed to upload ${file.name}`)
        }
      }

      // Make API request
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: input.trim(),
          role,
          testType,
          disableTools,
          files: fileIds
        }),
        signal: AbortSignal.timeout(300000) // 5 minute timeout for complex queries
      })
      
      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`)
      }
      
      const data: ApiResponse = await response.json()
      
      // Add assistant message
      const assistantMessage: Message = {
        role: "assistant",
        content: data.content,
        timestamp: new Date(data.timestamp),
        files: data.files
      }
      
      setMessages(prev => [...prev, assistantMessage])
      
      // Reset uploaded files after processing
      if (uploadedFiles.length > 0) {
        setUploadedFiles([])
      }
      
    } catch (error) {
      console.error('Error sending message:', error)
      
      // Provide specific error message based on error type
      if (error instanceof DOMException && error.name === 'TimeoutError') {
        toast.error("The request timed out. Your query may be too complex for the current timeout settings.")
        
        // Add the timeout error as a system message
        const errorMessage: Message = {
          role: "system",
          content: "The server request timed out. Complex queries like tables may take longer to process than the current timeout allows. Please try a simpler query or contact support.",
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
      } else {
        toast.error("Failed to get a response. Please try again.")
      }
    } finally {
      setIsLoading(false)
    }
  }

  // Get agent title based on role
  const getAgentTitle = () => {
    switch (role) {
      case "hr":
        return "HR Policy Agent"
      case "manager":
        return "Pay Calculation Agent"
      case "payroll":
        return "Analytics Agent"
      case "intelligent":
        return "Intelligent Supplemental Pay Agent"
      default:
        return "AI Agent"
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="sticky top-0 z-10 border-b border-border bg-background/80 backdrop-blur">
        <div className="container flex h-16 items-center justify-between px-4 sm:px-8">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2">
              <FiChevronLeft className="h-5 w-5" />
              <span className="hidden sm:inline">Back</span>
            </Link>
            <div className="flex items-center gap-2">
              <Image 
                src="/dxc-logo.svg"
                alt="DXC Logo"
                width={32}
                height={32}
                className="dark:invert"
              />
              <span className="font-medium">{getAgentTitle()}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="rounded-full p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
              aria-label="Agent settings"
            >
              <FiSettings className="h-5 w-5" />
            </button>
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="rounded-full p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? (
                <FiSun className="h-5 w-5" />
              ) : (
                <FiMoon className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>
      </header>
      
      {/* Settings panel */}
      {showSettings && (
        <div className="border-b border-border bg-secondary/10">
          <div className="container max-w-5xl py-4 px-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium">Agent Settings</h3>
              <button 
                onClick={() => setShowSettings(false)}
                className="text-muted-foreground hover:text-foreground"
                aria-label="Close settings"
                title="Close settings"
              >
                <FiX className="h-5 w-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Test Mode</label>
                <select 
                  value={testType}
                  onChange={(e) => setTestType(e.target.value)}
                  className="w-full sm:w-auto rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                  title="Test Mode Selection"
                  aria-label="Select test mode"
                >
                  {TEST_TYPES.map(type => (
                    <option key={type.id} value={type.id}>{type.label}</option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-muted-foreground">
                  {testType === 'excel' 
                    ? 'Excel Analysis mode: optimized for analyzing spreadsheet data' 
                    : testType === 'simple' 
                      ? 'Simple Query mode: basic questions without using tools'
                      : 'Standard mode: full agent capabilities'}
                </p>
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="disableTools"
                  checked={disableTools}
                  onChange={() => setDisableTools(!disableTools)}
                  className="mr-2 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
                <label htmlFor="disableTools" className="text-sm">
                  Disable tools (for debugging)
                </label>
              </div>
            </div>
          </div>
        </div>
      )}
      
      <main className="flex-1 overflow-hidden">
        <div className="container h-full max-w-5xl">
          <div className="flex h-[calc(100vh-4rem)] flex-col">
            {/* Chat messages */}
            <div className="flex-1 overflow-y-auto p-4">
              <div className="space-y-6">
                {messages.filter(m => m.role !== "system").map((message, i) => (
                  <div key={i} className={`flex ${message.role === "assistant" ? "justify-start" : "justify-end"}`}>
                    <div
                      className={`max-w-[85%] rounded-lg px-4 py-3 ${
                        message.role === "assistant"
                          ? "bg-muted text-foreground"
                          : "bg-primary text-primary-foreground"
                      }`}
                    >
                      {/* Files list */}
                      {message.files && message.files.length > 0 && (
                        <div className="mb-2 text-sm">
                          <div className="font-medium">Files:</div>
                          <ul className="list-disc list-inside opacity-80">
                            {message.files.map((file, fileIndex) => (
                              <li key={fileIndex}>{file}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {/* Message content */}
                      <div 
                        className="whitespace-pre-wrap message-content" 
                        dangerouslySetInnerHTML={{ __html: formatTableContent(message.content) }}
                      />
                      
                      {/* Timestamp */}
                      <div className="mt-1 text-right text-xs opacity-70">
                        {message.timestamp.toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit"
                        })}
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="max-w-[85%] rounded-lg bg-muted px-4 py-3 text-foreground">
                      <div className="flex space-x-2">
                        <div className="h-2 w-2 animate-pulse rounded-full bg-foreground/60"></div>
                        <div className="h-2 w-2 animate-pulse rounded-full bg-foreground/60" style={{ animationDelay: "0.2s" }}></div>
                        <div className="h-2 w-2 animate-pulse rounded-full bg-foreground/60" style={{ animationDelay: "0.4s" }}></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messageEndRef} />
              </div>
            </div>
            
            {/* Input area */}
            <div className="border-t border-border bg-card p-4">
              {/* Uploaded files */}
              {uploadedFiles.length > 0 && (
                <div className="mb-3 rounded-md bg-secondary/10 p-3">
                  <div className="mb-1 font-medium text-sm">Uploaded Files:</div>
                  <ul className="space-y-1">
                    {uploadedFiles.map((file, index) => (
                      <li key={index} className="flex items-center justify-between text-sm">
                        <span className="truncate">{file.name}</span>
                        <button 
                          onClick={() => removeFile(index)}
                          className="ml-2 text-muted-foreground hover:text-destructive"
                          aria-label={`Remove ${file.name}`}
                        >
                          <FiX className="h-4 w-4" />
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {/* Test type indicator */}
              {testType !== "default" && (
                <div className="mb-3 text-xs font-medium text-secondary">
                  <span className="inline-flex items-center gap-1 rounded-full bg-secondary/20 px-2 py-1">
                    {testType === "excel" ? "Excel Analysis Mode" : "Simple Query Mode"}
                  </span>
                </div>
              )}
              
              <form onSubmit={handleSubmit} className="flex gap-2">
                <input 
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  className="hidden"
                  multiple
                  title="Upload files"
                  aria-label="Upload files"
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex-none rounded-md border border-input bg-background p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  disabled={isLoading}
                  aria-label="Upload files"
                >
                  <FiUpload className="h-5 w-5" />
                </button>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type your message..."
                  className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  className="flex-none rounded-md bg-primary p-2 text-primary-foreground hover:bg-primary/90"
                  disabled={isLoading}
                  aria-label="Send message"
                >
                  <FiSend className="h-5 w-5" />
                </button>
              </form>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
} 