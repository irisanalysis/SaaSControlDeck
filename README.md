# SaaS Control Deck

[![Deployment Status](https://img.shields.io/badge/deployment-active-brightgreen)](https://saascontrol3.vercel.app)
[![Framework](https://img.shields.io/badge/frontend-Next.js%2015.3.3-black)](https://nextjs.org/)
[![Backend](https://img.shields.io/badge/backend-Python%20FastAPI-blue)](https://fastapi.tiangolo.com/)
[![AI Integration](https://img.shields.io/badge/AI-Google%20Genkit-orange)](https://firebase.google.com/docs/genkit)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A modern full-stack AI-powered SaaS platform with a responsive dashboard, distributed Python backend, and intelligent contextual assistance.

## 🚀 Live Demo

**Production Deployment:** [https://saascontrol3.vercel.app](https://saascontrol3.vercel.app)

## 📋 Project Overview

SaaS Control Deck is a comprehensive AI data analysis platform built with modern technologies and a microservices architecture. The project features a sleek Next.js frontend with Google Genkit AI integration and a distributed Python backend with FastAPI microservices.

### Key Features

- **Modern Frontend**: Next.js 15.3.3 with TypeScript, Tailwind CSS, and Radix UI components
- **AI Integration**: Google Genkit with Gemini 2.5 Flash for contextual help and data analysis
- **Distributed Backend**: Python FastAPI microservices with isolated project instances
- **Comprehensive UI**: Responsive dashboard with sidebar navigation and customizable components
- **Production Ready**: Deployed on Vercel with comprehensive monitoring and logging

## 🏗️ Architecture

### Frontend Stack
- **Framework**: Next.js 15.3.3 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom theme system
- **UI Components**: Radix UI primitives with custom components
- **AI Integration**: Google Genkit for AI flows and contextual assistance
- **Icons**: Lucide React icons

### Backend Stack
- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.11
- **Database**: PostgreSQL 15 with asyncpg
- **Cache**: Redis 7 for sessions and rate limiting
- **Storage**: MinIO S3-compatible object storage
- **AI/ML**: OpenAI API, Ray distributed computing
- **Monitoring**: Prometheus metrics, structured logging

## 📁 Project Structure

```
saas-control-deck/
├── frontend/                    # Next.js frontend application
│   ├── src/
│   │   ├── app/                # Next.js App Router pages
│   │   ├── components/         # React components
│   │   │   ├── ui/            # Base UI components (Radix UI)
│   │   │   ├── dashboard/     # Dashboard-specific components
│   │   │   ├── layout/        # Layout components
│   │   │   └── ai/            # AI integration components
│   │   ├── ai/                # Google Genkit AI flows
│   │   ├── lib/               # Utility functions
│   │   └── hooks/             # Custom React hooks
│   ├── next.config.ts         # Next.js configuration
│   ├── tailwind.config.ts     # Tailwind CSS configuration
│   └── package.json           # Frontend dependencies
├── backend/                     # Python backend services
│   ├── backend-pro1/           # Project 1 (Ports 8000-8099)
│   │   ├── api-gateway/       # API Gateway service
│   │   ├── data-service/      # Data processing service
│   │   ├── ai-service/        # AI analysis service
│   │   ├── shared/            # Shared components
│   │   └── docker-compose.yml # Service orchestration
│   ├── backend-pro2/           # Project 2 (Ports 8100-8199)
│   ├── scripts/               # Management scripts
│   └── CLAUDE.md              # Backend development guide
├── .docs/                      # Comprehensive documentation
│   ├── CICD/                  # CI/CD and deployment guides
│   ├── architecture/          # System architecture docs
│   └── versions/              # Version management
├── package.json               # Root package configuration
├── vercel.json                # Vercel deployment config
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 20+ and npm
- **Python** 3.11+ (for backend development)
- **Docker** and Docker Compose (for backend services)

### Frontend Development

```bash
# Clone the repository
git clone <repository-url>
cd saas-control-deck

# Install dependencies
npm install

# Start development server (Firebase Studio auto-manages this)
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Backend Development

```bash
# Navigate to backend directory
cd backend

# Setup environment (interactive script)
./scripts/setup.sh

# Start services (choose project instance)
./scripts/start-dev.sh

# View service status
./scripts/status.sh

# Stop all services
./scripts/stop-dev.sh
```

## 🔧 Development Environment

### Firebase Studio Integration

This project runs in Firebase Studio's Nix architecture environment:

- **Development Port**: 9000 (auto-managed by Firebase Studio)
- **Preview System**: Automatic proxy to development server
- **Configuration**: `.idx/dev.nix` controls development environment
- **Important**: Never manually run `npm run dev` in Firebase Studio - it's auto-managed

### Backend Port Allocation

**Project 1 (backend-pro1)**: Ports 8000-8099
- API Gateway: 8000
- Data Service: 8001
- AI Service: 8002
- PostgreSQL: 5432, Redis: 6379, MinIO: 9000/9001

**Project 2 (backend-pro2)**: Ports 8100-8199
- API Gateway: 8100
- Data Service: 8101
- AI Service: 8102
- PostgreSQL: 5433, Redis: 6380, MinIO: 9002/9003

## 🎨 UI Component System

The application uses a consistent design system built on Radix UI primitives:

### Base Components
- Buttons, Forms, Dialogs, Tooltips
- Cards, Tabs, Accordions, Carousels
- Navigation, Sidebar, Layout components

### Dashboard Components
- Profile cards, Settings cards
- Integrations, Device management
- Pending approvals, Analytics widgets

### Theme System
- CSS variables for consistent theming
- Dark mode support (class-based)
- Responsive design with mobile-first approach
- Custom Tailwind configuration with design tokens

## 🤖 AI Integration

### Google Genkit Integration
- **Model**: Gemini 2.5 Flash
- **Contextual Help**: Floating AI assistant button
- **Configuration**: `src/ai/genkit.ts`
- **Flows**: Defined in `src/ai/flows/`

### Development Commands
```bash
# Start Genkit development server
npm run genkit:dev

# Start Genkit with file watching
npm run genkit:watch
```

## 📦 Deployment

### Vercel Deployment (Production)

**Current Status**: ✅ Successfully deployed at [https://saascontrol3.vercel.app](https://saascontrol3.vercel.app)

**Configuration**:
```json
{
  "framework": "nextjs",
  "functions": {"src/app/api/**/*.ts": {"runtime": "@vercel/node"}},
  "env": {
    "NODE_ENV": "production",
    "NEXT_PUBLIC_APP_NAME": "SaaS Control Deck"
  }
}
```

**Build Command**: `npm run vercel-build`
**Root Directory**: `frontend`

### Docker Deployment (Backend)

```bash
# Build and start all services
cd backend/backend-pro1
docker-compose up -d

# View logs
docker-compose logs -f

# Health check
curl http://localhost:8000/health
```

## 📚 Documentation

### Comprehensive Guides
- **[Backend Architecture Guide](backend/CLAUDE.md)** - Complete backend development guide
- **[Vercel Deployment Guide](.docs/CICD/vercel/README.md)** - Deployment troubleshooting and setup
- **[System Architecture](.docs/architecture/SYSTEM_ARCHITECTURE.md)** - High-level system overview

### API Documentation
- **API Gateway**: `http://localhost:8000/docs` (when running)
- **Data Service**: `http://localhost:8001/docs`
- **AI Service**: `http://localhost:8002/docs`

### Development References
- **Frontend Development**: See `CLAUDE.md` for detailed patterns and guidelines
- **Component Library**: All UI components documented in `src/components/ui/`
- **AI Integration**: Google Genkit flows in `src/ai/flows/`

## 🔍 Troubleshooting

### Common Issues

**Deployment Issues**:
- Check [Vercel Troubleshooting Guide](.docs/CICD/vercel/VERCEL_DEPLOYMENT_TROUBLESHOOTING.md)
- Verify `vercel.json` configuration
- Ensure root directory is set to `frontend`

**Development Issues**:
- Backend services: Use `./scripts/status.sh` to check service health
- Frontend: Check Firebase Studio preview system
- Module resolution: Verify path aliases in `next.config.ts`

### Health Checks
```bash
# Frontend
curl http://localhost:9000

# Backend services
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## 🧪 Testing

### Frontend Testing
```bash
# Type checking
npm run typecheck

# Linting
npm run lint

# Build verification
npm run build
```

### Backend Testing
```bash
# Unit tests
cd backend/backend-pro1
pytest

# API testing
curl http://localhost:8000/api/v1/health

# Load testing
ab -n 1000 -c 10 http://localhost:8000/api/v1/auth/me
```

## 🤝 Contributing

### Development Workflow

1. **Frontend Changes**: Work in `frontend/src/` directory
2. **Backend Changes**: Work in `backend/` directory with appropriate project instance
3. **Documentation**: Update relevant guides in `.docs/`
4. **Testing**: Ensure all tests pass before committing

### Code Style
- **TypeScript**: Strict mode enabled, proper type definitions required
- **Python**: Follow PEP 8, use async patterns
- **Components**: Follow established UI component patterns
- **Imports**: Use relative paths, avoid path aliases in production builds

## 🗺️ Roadmap

### Current Status
- ✅ Frontend deployed on Vercel
- ✅ Backend microservices architecture complete
- ✅ AI integration with Google Genkit
- ✅ Comprehensive documentation system

### Planned Features
- 📋 GitHub Actions CI/CD pipeline
- 📋 Advanced AI analytics dashboard
- 📋 Multi-tenant user management
- 📋 Real-time collaboration features
- 📋 Mobile application

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Support

For questions, issues, or contributions:

1. **Documentation**: Check `.docs/` directory for comprehensive guides
2. **Issues**: Create detailed issue reports with reproduction steps
3. **Development**: Follow the development guides in `CLAUDE.md` and `backend/CLAUDE.md`

---

**Built with**: Next.js, Python FastAPI, Google Genkit, Vercel  
**Architecture**: Full-stack monorepo with microservices backend  
**Status**: Production deployment active on Vercel

*Last updated: December 2024*