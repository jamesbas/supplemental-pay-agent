# DXC Supplemental Pay Agent UI

A modern Next.js UI for interacting with the DXC Supplemental Pay AI Agent system featuring dark/light mode support.

## Features

- Dark/light mode interface with theme toggling
- Chat-based interaction with AI agents
- Role-based access:
  - HR Team (policy information)
  - People Manager (pay calculations and approvals)
  - Payroll Manager (data analytics and compliance)
  - Intelligent Supplemental Pay (comprehensive agent for all questions)
- File upload functionality for document analysis
- Test modes:
  - Standard Mode (default)
  - Excel Analysis (optimized for spreadsheets)
  - Simple Query (basic questions without tools)
- Responsive design for desktop and mobile
- Agent settings panel for configuration

## Getting Started

### Prerequisites

- Node.js 18.0.0 or later
- npm or yarn

### Installation

1. Install dependencies:

```bash
cd ui
npm install
# or
yarn install
```

2. Configure environment variables by creating a `.env.local` file:

```
# API Configuration
NEXT_PUBLIC_API_URL=http://127.0.0.1:5000/api
BACKEND_API_URL=http://127.0.0.1:5000/api

# Application Settings
NEXT_PUBLIC_SITE_NAME=DXC Supplemental Pay AI
```

3. Start the development server:

```bash
npm run dev
# or
yarn dev
```

4. Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Project Structure

```
ui/
├── app/                 # Next.js app router
│   ├── api/             # API routes
│   ├── chat/            # Chat interface
│   │   └── page.tsx     # Main chat application
│   ├── components/      # Shared components
│   ├── context/         # Context providers
│   │   └── theme-provider.tsx # Theme context
│   ├── lib/             # Utility functions
│   ├── layout.tsx       # Root layout
│   └── page.tsx         # Home page with role selection
├── public/              # Static assets
│   └── dxc-logo.svg     # DXC logo
├── styles/              # Global styles
│   └── globals.css      # Global CSS and Tailwind imports
├── next.config.js       # Next.js configuration
└── package.json         # Project dependencies
```

## Key Dependencies

- **Next.js** - React framework with app router
- **React** - UI library
- **TailwindCSS** - Utility-first CSS framework
- **React Icons** - Icon library
- **Sonner** - Toast notifications
- **Next Themes** - Theme management
- **Axios** - HTTP client
- **React Markdown** - Markdown rendering

## Connecting to the Agent Backend

The UI connects to the Python backend via API. Make sure the backend server is running and accessible at the URL specified in your `.env.local` file.

## License

This project is proprietary to DXC Technology. 