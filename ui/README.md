# DXC Supplemental Pay Agent UI

A dark mode Next.js UI for testing the DXC Supplemental Pay AI Agent system.

## Features

- Dark mode interface
- Chat-based interaction with AI agents
- Role-based access (HR Team, People Manager, Payroll Manager)
- File upload for testing without SharePoint
- Responsive design for desktop and mobile

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
NEXT_PUBLIC_API_URL=http://localhost:5000/api
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
│   ├── components/      # Shared components
│   ├── context/         # Context providers
│   ├── lib/             # Utility functions
│   ├── layout.tsx       # Root layout
│   └── page.tsx         # Home page
├── public/              # Static assets
├── styles/              # Global styles
├── next.config.js       # Next.js configuration
└── package.json         # Project dependencies
```

## Connecting to the Agent Backend

The UI connects to the Python backend via API. Make sure the backend server is running and accessible at the URL specified in your `.env.local` file.

## License

This project is proprietary to DXC Technology. 