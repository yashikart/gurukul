# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Quick Start Commands

### Development Environment Setup
```bash
# Backend - Start all services (8 microservices)
cd Backend
start_all_services.bat

# Frontend - Start React development server
cd "new frontend"  
start_frontend.bat

# Health check all services
check_health.bat
```

### Production Deployment
```bash
# Full production deployment
deploy_production.bat

# Docker deployment
docker-compose up -d

# Service-specific deployments
cd Backend && deploy_production.bat
cd "new frontend" && deploy_production.bat
```

### Testing and Development
```bash
# Backend dependency management
cd Backend && install_all_dependencies.bat

# Fix missing dependencies
fix_missing_dependencies.bat

# Frontend development
cd "new frontend"
npm run dev        # Development server
npm run build      # Production build
npm run lint       # ESLint checking

# Backend testing
cd Backend
python test_api.py
python health_check_services.py
```

## Architecture Overview

### Microservices Architecture
This is a sophisticated AI-powered educational platform built with a microservices architecture:

**Backend Services (Python/FastAPI):**
- **Base Backend (8000)** - Main API with orchestration integration, handles subjects, lectures, tests
- **API Data Service (8001)** - RAG processing, LLM services, chatbot functionality  
- **Financial Simulator (8002)** - LangGraph-based financial forecasting with Prophet/ARIMA models
- **Memory Management (8003)** - User session persistence, conversation history
- **Akash Service (8004)** - Authentication gateway and memory coordination
- **Subject Generation (8005)** - AI-powered educational content generation
- **Wellness API + Forecasting (8006)** - Health metrics with advanced forecasting
- **TTS Service (8007)** - Text-to-speech capabilities

**Frontend (React/Vite):**
- Modern React application with TypeScript
- 3D visualizations using Three.js (@react-three/fiber)
- Real-time agent simulation dashboard
- Financial forecasting interface
- Multilingual educational interface

**Infrastructure:**
- MongoDB for data persistence across all services
- Redis for caching and session management
- Supabase for authentication
- Docker containerization with health checks

### Key Integration Systems

**Orchestration Engine:**
- Unified orchestration system coordinates all services
- Agent memory management across services
- Real-time decision visualization
- Trigger-based workflow automation

**AI/ML Pipeline:**
- RAG (Retrieval-Augmented Generation) for educational content
- Multiple LLM integrations: Groq, OpenAI, Gemini
- Vector stores: FAISS, Chroma, Pinecone, Weaviate
- Advanced forecasting: Prophet, ARIMA, statistical models

**Financial Simulation:**
- Multi-agent financial planning workflow
- LangGraph implementation for complex workflows
- Real-time risk assessment and trend analysis
- Interactive dashboards with Recharts

## Technology Stack Specifics

### Backend Dependencies (Python)
- **Web Framework:** FastAPI with Uvicorn
- **AI/ML:** LangChain ecosystem, Transformers, Sentence-Transformers
- **Computer Vision:** OpenCV, EasyOCR, PaddleOCR, PyMuPDF
- **Financial Analysis:** Prophet, yfinance, alpha-vantage
- **Database:** PyMongo, Redis client
- **Audio:** gTTS, pyttsx3, SpeechRecognition

### Frontend Dependencies (Node.js)
- **Framework:** React 18+ with Vite
- **Routing:** React Router v7
- **State Management:** Redux Toolkit with Redux Persist
- **UI Libraries:** Tailwind CSS, Lucide React
- **3D Graphics:** Three.js, React Three Fiber
- **Data Visualization:** Recharts
- **Internationalization:** i18next, react-i18next

### Development Environment Requirements
- Python 3.9+ (backend services)
- Node.js 20+ (frontend)
- MongoDB (data persistence)
- Redis (caching/sessions)
- API keys: Groq, OpenAI, Gemini, Supabase

## Service Communication Patterns

### API Integration
- All services expose `/health` endpoints
- RESTful APIs with FastAPI automatic documentation at `/docs`
- CORS configured for cross-origin requests from frontend
- JWT-based authentication via Supabase
- Unified error handling with trace IDs

### Data Flow
1. **Frontend** makes requests to Base Backend (8000)
2. **Base Backend** coordinates with other services via HTTP
3. **Orchestration Engine** manages complex workflows
4. **Memory Management** persists user interactions
5. **Financial Simulator** runs independent agent workflows

### Key Architectural Patterns
- **Microservices:** Independent services with clear boundaries
- **Event-Driven:** Orchestration triggers based on thresholds
- **RAG Pipeline:** Document retrieval + LLM generation
- **Agent-Based:** Multiple AI agents with specialized roles

## File Structure Context

```
Gurukul_new-main/
├── Backend/                     # All microservices
│   ├── Base_backend/           # Main API (port 8000)
│   ├── api_data/              # Data processing service  
│   ├── Financial_simulator/    # LangGraph financial workflows
│   ├── memory_management/      # User session persistence
│   ├── akash/                 # Auth gateway
│   ├── subject_generation/     # Content generation
│   ├── orchestration/         # Unified orchestration system
│   └── start_all_services.bat # Master startup script
├── new frontend/              # React application
│   ├── src/pages/            # Route components
│   ├── src/components/       # Reusable UI components
│   └── src/api/              # Backend integration layer
├── docker-compose.yml        # Production containerization
├── .env.example             # Environment variable template
└── monitoring/              # Service monitoring and health
```

## Common Development Workflows

### Adding New AI Features
1. Implement in appropriate microservice (typically Base_backend or api_data)
2. Add orchestration triggers if needed in `orchestration/` 
3. Update frontend API integration in `src/api/`
4. Test with individual service and full integration

### Database Schema Changes
1. Update models in respective service's database module
2. Consider impact on Memory Management service (8003)
3. Update orchestration database integration if needed
4. Test data migration with existing user sessions

### Frontend Component Development  
1. Create components in `src/components/`
2. Add pages in `src/pages/`  
3. Integrate with backend APIs via `src/api/`
4. Ensure responsive design with Tailwind classes

### Service Orchestration Updates
1. Modify orchestration config in `Backend/orchestration/`
2. Update trigger thresholds and workflows
3. Test agent coordination across services
4. Verify memory persistence across agent interactions

## Environment Configuration

### Critical Environment Variables
- `GROQ_API_KEY` - Primary LLM service
- `MONGODB_URI` - Database connection
- `SUPABASE_URL` & `SUPABASE_ANON_KEY` - Authentication  
- `REDIS_PASSWORD` - Caching service
- `ALLOWED_ORIGINS` - CORS configuration

### Service-Specific Configuration
Each microservice may have additional environment requirements. Check individual service `.env.example` files and the centralized configuration in `Backend/shared_config.py`.

## Troubleshooting Guidelines

### Service Startup Issues
- Use `health_check_services.py` to diagnose service status
- Check individual service logs in their directories
- Verify port availability (8000-8007)
- Ensure MongoDB and Redis are running

### Integration Problems
- Check orchestration integration status at `/integration-status`
- Verify API endpoints with `/docs` on each service
- Test individual services before full system integration
- Monitor memory management service for session persistence

### Frontend Issues
- Verify backend services are running on expected ports
- Check browser console for API connection errors
- Ensure environment variables are properly loaded
- Test API endpoints independently with tools like Postman

## Testing Strategy

### Backend Testing
- Individual service health checks
- API endpoint testing with FastAPI test client
- Agent workflow validation
- Database integration testing

### Frontend Testing
- Component unit testing with React Testing Library
- API integration testing
- User interaction flow testing
- Cross-browser compatibility

### System Integration Testing
- Full service orchestration testing
- End-to-end user workflows
- Performance testing under load
- Agent coordination and memory persistence
