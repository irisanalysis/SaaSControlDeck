# CLAUDE.md - Backend Architecture Guide

This file provides guidance to Claude Code (claude.ai/code) when working with the distributed Python backend architecture in this repository.

## Project Architecture Overview

This is a scalable distributed Python backend system supporting multi-project isolated deployment, designed specifically for AI data analysis platforms.

### Core Features

- **Multi-project Isolation**: Support for independent project instances (backend-pro1, backend-pro2), avoiding resource conflicts
- **Microservices Architecture**: API Gateway, Data Service, AI Service deployed independently
- **Containerized Deployment**: Complete Docker + Docker Compose support
- **AI Integration**: OpenAI API, Ray distributed computing integration
- **Observability**: Prometheus monitoring, structured logging, health checks
- **Production Ready**: Complete security, rate limiting, error handling mechanisms

### Port Allocation Strategy

**Project 1 (backend-pro1)**: Ports 8000-8099
- API Gateway: 8000
- Data Service: 8001
- AI Service: 8002
- PostgreSQL: 5432
- Redis: 6379
- MinIO: 9000/9001
- Prometheus: 9090

**Project 2 (backend-pro2)**: Ports 8100-8199
- API Gateway: 8100
- Data Service: 8101
- AI Service: 8102
- PostgreSQL: 5433
- Redis: 6380
- MinIO: 9002/9003
- Prometheus: 9091

## Project Structure

```
backend/
├── backend-pro1/          # Project 1 (Ports 8000-8099)
│   ├── api-gateway/       # API Gateway Service
│   │   ├── app/
│   │   │   ├── main.py    # FastAPI application entry
│   │   │   ├── core/      # Core modules (exception handling, etc.)
│   │   │   └── routers/   # Route modules (auth, users, projects, analysis)
│   ├── data-service/      # Data Processing Service
│   │   └── app/
│   │       ├── main.py    # Data service entry
│   │       └── routers/   # Data upload, management, processing
│   ├── ai-service/        # AI Analysis Service
│   │   └── app/
│   │       ├── main.py    # AI service entry
│   │       └── routers/   # AI analysis, model management, distributed tasks
│   ├── shared/            # Shared Components
│   │   ├── config.py      # Configuration management
│   │   ├── auth.py        # JWT authentication
│   │   ├── database.py    # PostgreSQL connection pool
│   │   ├── redis_client.py # Redis client
│   │   ├── logging.py     # Structured logging
│   │   ├── middleware/    # Middleware (request ID, metrics, rate limiting)
│   │   └── models/        # Data models
│   ├── scripts/           # Database migration scripts
│   ├── .env.example       # Environment variables template
│   ├── requirements.txt   # Python dependencies
│   ├── docker-compose.yml # Service orchestration
│   └── Dockerfile         # Container image
├── backend-pro2/          # Project 2 (Ports 8100-8199)
│   └── [Same structure, different port configuration]
├── scripts/               # Management scripts
│   ├── setup.sh          # Environment initialization
│   ├── start-dev.sh      # Start development environment
│   ├── stop-dev.sh       # Stop services
│   └── status.sh         # View status
├── config/               # Global configuration
├── deployments/          # Kubernetes deployment files
├── monitoring/           # Monitoring configuration
├── README.md             # Project overview
└── DEPLOYMENT_GUIDE.md   # Detailed deployment guide
```

## Technology Stack

### Core Framework
- **FastAPI 0.104.1** - Modern async web framework
- **uvicorn** - ASGI server
- **Python 3.11** - Runtime environment

### Data Storage
- **PostgreSQL 15** - Primary database
- **Redis 7** - Cache and session management
- **MinIO** - S3-compatible object storage

### AI and Computing
- **OpenAI API** - GPT model integration
- **Ray 2.8.0** - Distributed computing framework
- **numpy, pandas, scikit-learn** - Data science libraries

### Authentication and Security
- **JWT (python-jose)** - Token authentication
- **bcrypt (passlib)** - Password encryption
- **Rate limiting middleware** - Redis distributed rate limiting

### Monitoring and Logging
- **Prometheus** - Metrics collection
- **structlog** - Structured logging
- **Sentry** - Error tracking

### Containerization
- **Docker** - Containerized deployment
- **Docker Compose** - Service orchestration

## Development Environment Configuration

### Quick Start

```bash
cd backend

# 1. Initialize environment
./scripts/setup.sh

# 2. Start services (interactive selection)
./scripts/start-dev.sh

# 3. View status
./scripts/status.sh
```

### Environment Variables Configuration

Each project has independent `.env` files, copied from `.env.example`:

```bash
# Project 1 configuration example (backend-pro1/.env)
PROJECT_ID=pro1
API_GATEWAY_PORT=8000
DATABASE_URL=postgresql+asyncpg://postgres:postgres123@localhost:5432/ai_platform_pro1
REDIS_URL=redis://:redis123@localhost:6379/0
SECRET_KEY=your-super-secret-key-32-chars-minimum
OPENAI_API_KEY=your_openai_api_key_here
```

### Docker Service Orchestration

Each project includes complete `docker-compose.yml` with:
- PostgreSQL database
- Redis cache
- MinIO object storage
- API Gateway, Data Service, AI Service
- Celery async task queue
- Prometheus monitoring

## API Architecture Design

### Authentication Flow
1. User registration: `POST /api/v1/auth/register`
2. User login: `POST /api/v1/auth/login`
3. Token refresh: `POST /api/v1/auth/refresh`
4. Get user info: `GET /api/v1/auth/me`

### Core API Endpoints

**API Gateway (8000/8100)**
- `/api/v1/auth/*` - Authentication related
- `/api/v1/users/*` - User management
- `/api/v1/projects/*` - Project management
- `/api/v1/analysis/*` - Data analysis

**Data Service (8001/8101)**
- `/upload/file` - File upload
- `/manage/datasets` - Dataset management
- `/process/*` - Data processing

**AI Service (8002/8102)**
- `/analysis/*` - AI analysis
- `/models/*` - Model management
- `/tasks/*` - Distributed tasks

### Database Schema

Main table structure:
- `users` - User main table
- `user_profiles` - User profiles
- `projects` - Project management
- `datasets` - Datasets
- `analysis_tasks` - Analysis tasks
- `analysis_results` - Analysis results
- `api_logs` - API call logs

## Shared Components Details

### Configuration Management (`shared/config.py`)
- Use Pydantic Settings to manage configuration
- Automatic environment variable validation and type conversion
- Support for multi-environment configuration

### Authentication System (`shared/auth.py`)
- JWT token management (access token 30 minutes, refresh token 7 days)
- bcrypt password encryption
- Bearer Token based API authentication

### Database Layer (`shared/database.py`)
- asyncpg async PostgreSQL connection pool
- Automatic connection management and error handling
- Transaction context manager

### Redis Client (`shared/redis_client.py`)
- Async Redis operations
- JSON serialization/deserialization
- Connection pool and reconnection mechanism

### Middleware System

**Request ID Middleware** (`shared/middleware/request_id.py`)
- Generate unique ID for each request
- Used for log tracking and debugging

**Metrics Middleware** (`shared/middleware/metrics.py`)
- Prometheus metrics collection
- Request counting, response time, active connections
- Slow request detection and alerting

**Rate Limiting Middleware** (`shared/middleware/rate_limit.py`)
- Redis distributed rate limiting
- Limits based on IP or user ID
- Sliding window algorithm

## Monitoring and Logging

### Prometheus Metrics
- HTTP request statistics
- Response time distribution
- Error rate monitoring
- System resource usage

### Structured Logging
- Use structlog for structured logging
- JSON format for easy analysis
- Include request ID for trace tracking

### Health Checks
- Basic health check: `/health`
- Detailed health check: `/health/detailed`
- Readiness check: `/ready` (used by Kubernetes)

## Development and Deployment Process

### Local Development
1. Modify code
2. Container auto-restart (volume mounting)
3. View logs: `docker-compose logs -f [service]`

### Testing
```bash
# Unit tests
pytest

# API testing
curl http://localhost:8000/health

# Load testing
ab -n 1000 -c 10 http://localhost:8000/api/v1/auth/me
```

### Production Deployment
1. Set production environment variables
2. Build production images
3. Use Kubernetes deployment configuration
4. Configure monitoring and alerting

## Common Development Tasks

### Adding New API Endpoints
1. Create route file in corresponding service's `routers/` directory
2. Define Pydantic models for request/response validation
3. Register route in `main.py`
4. Add corresponding database operations
5. Write unit tests

### Adding New Middleware
1. Create middleware file in `shared/middleware/`
2. Inherit from `BaseHTTPMiddleware`
3. Register in `main.py` (pay attention to order)

### Database Migration
1. Modify `scripts/init-db.sql`
2. Restart database container to apply changes
3. Or use Alembic for version migration

### Adding New Service
1. Copy existing service directory structure
2. Modify ports and configuration
3. Add service definition in docker-compose.yml
4. Update health checks and monitoring

## Error Handling and Debugging

### Exception Handling System
- Custom exception classes (`APIException`)
- Global exception handlers
- Standardized error response format

### Debugging Tools
- Detailed error logs
- Request ID trace tracking
- Prometheus metrics analysis
- Container debugging: `docker-compose exec [service] bash`

### Common Issue Troubleshooting
1. **Port conflicts**: Check port usage `lsof -i :8000`
2. **Database connection**: View database logs `docker-compose logs postgres`
3. **Redis connection**: Test connection `docker-compose exec redis redis-cli ping`
4. **Slow service startup**: View specific service logs

## Performance Optimization

### Database Optimization
- Connection pool configuration optimization
- Appropriate index strategy
- Query optimization and N+1 problem avoidance

### Caching Strategy
- Redis user session cache
- API response cache
- Database query result cache

### Async Processing
- All IO operations use async
- Celery handles long-running tasks
- Ray distributed computing

### Container Optimization
- Multi-stage build reduces image size
- Run as non-root user
- Health checks and resource limits

## Security Best Practices

### Authentication Security
- JWT token short-term expiry
- Secure key management
- Password strength validation

### Network Security
- CORS configuration
- Rate limiting protection
- Input validation and SQL injection prevention

### Container Security
- Minimal base images
- Run as non-privileged user
- Security scanning and updates

---

## Important Reminders

⚠️ **Environment Variable Configuration**
- Production environment must set strong passwords and keys
- `OPENAI_API_KEY` is required for AI functionality
- Database and Redis passwords should be rotated regularly

✅ **Development Best Practices**
- Prioritize using existing shared components
- Follow async programming patterns
- Add appropriate error handling and logging
- Write unit tests covering core functionality

🔧 **Troubleshooting**
- Use `./scripts/status.sh` to view overall status
- View specific service logs to locate issues
- Use health check endpoints for diagnosis
- Monitor Prometheus metrics to identify performance bottlenecks