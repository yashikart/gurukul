# Gurukul Frontend

Modern React frontend for the Gurukul Learning Platform with AI agent simulation capabilities.

## Features

### 🤖 AI Agent Simulation
- **FinancialCrew**: Blue theme with finance icon
- **EduMentor**: Green theme with book icon
- **WellnessBot**: Orange/purple theme with heart icon
- Real-time agent decision visualization
- Interactive timeline of user-agent exchanges
- Dynamic feedback indicators

### 📊 Dashboards
- **Forecasting Dashboard**: Financial and data forecasting
- **Agent Simulator**: Real-time agent visualization
- **User Progress**: Learning analytics and progress tracking
- **Educational Interface**: Lesson generation and learning tools

### 🎓 Educational Features
- AI-powered lesson generation
- Interactive quiz system
- Progress tracking
- Multilingual support

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Or use the batch script
start_frontend.bat
```

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Redux Toolkit** - State management
- **React Router** - Navigation
- **Supabase** - Authentication and data storage

## Project Structure

```
src/
├── components/          # Reusable UI components
├── pages/              # Page components
├── api/                # API integration
├── hooks/              # Custom React hooks
├── styles/             # CSS and styling
├── utils/              # Utility functions
└── store/              # Redux store configuration
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm test` - Run tests
- `npm run lint` - Run ESLint

## Environment Variables

Create a `.env` file with your Supabase credentials:

```env
VITE_SUPABASE_URL=https://aczmbrhfzankcvpbjavt.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjem1icmhmemFua2N2cGJqYXZ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1Njg1MDIsImV4cCI6MjA4MDE0NDUwMn0.PsCxt3xyBGlh6BskcqDH5ojPLDjWRLMwgNYW-8eKBys
VITE_API_BASE_URL=http://localhost:8000
```

## Integration with Backend

The frontend communicates with backend services through:

- **REST APIs**: Standard HTTP requests
- **WebSocket**: Real-time updates
- **Authentication**: Supabase JWT tokens

## Key API Endpoints

- `/get_agent_output` - Agent decisions and outputs
- `/agent_logs` - Agent activity logs
- `/user_meta` - User profile information
- `/subjects` - Educational subjects
- `/generate-lesson` - AI lesson generation
- `/simulate` - Financial simulation

## Deployment

### Development
```bash
npm run dev
```

### Production
```bash
npm run build
npm run preview
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## Technology Stack

- React with Vite for fast development
- Tailwind CSS for styling
- GSAP for animations
- React Query for data fetching
- Supabase for authentication and data storage

## Supabase Setup

This project now uses Supabase for authentication and data storage. See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for detailed setup instructions.

The project is configured to use the following Supabase project:
- **Project URL**: https://aczmbrhfzankcvpbjavt.supabase.co
- **Anonymous Key**: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjem1icmhmemFua2N2cGJqYXZ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1Njg1MDIsImV4cCI6MjA4MDE0NDUwMn0.PsCxt3xyBGlh6BskcqDH5ojPLDjWRLMwgNYW-8eKBys