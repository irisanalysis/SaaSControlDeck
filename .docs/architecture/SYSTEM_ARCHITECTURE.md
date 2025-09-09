# System Architecture - SaaSControlDeck

## Overview

SaaSControlDeck is a full-stack AI data analysis platform built with a modern microservices architecture, designed for rapid development cycles and enterprise-scale deployment.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer / CDN                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   Frontend (Port 9000)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │   Next.js   │ │  Radix UI   │ │   Google Genkit     │   │
│  │  15.3.3     │ │ Components  │ │   (AI Integration)  │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                  API Gateway                                │
│                 (Port 8000)                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼──────┐ ┌────────▼────────┐ ┌──────▼──────┐
│ Data Service │ │   AI Service    │ │   Backend   │
│(Port 8001)   │ │  (Port 8002)    │ │   Pro2      │
└───────┬──────┘ └────────┬────────┘ │(Port 8100)  │
        │                 │          └─────────────┘
        │                 │
┌───────▼──────┐ ┌────────▼────────┐
│  PostgreSQL  │ │  Ray Cluster    │
│   Database   │ │ (Distributed    │
│              │ │  Computing)     │
└──────────────┘ └─────────────────┘
        │                 
┌───────▼──────┐          
│    Redis     │          
│   (Cache)    │          
└──────────────┘          
        │                 
┌───────▼──────┐          
│    MinIO     │          
│ (S3 Storage) │          
└──────────────┘          
```

## Technology Stack

### Frontend
- **Framework**: Next.js 15.3.3 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with CSS variables
- **UI Components**: Radix UI primitives
- **AI Integration**: Google Genkit with Gemini 2.5 Flash
- **Development**: Firebase Studio Nix environment

### Backend
- **API Framework**: FastAPI (Python 3.11+)
- **Architecture**: Microservices with API Gateway pattern
- **Databases**: PostgreSQL (primary), Redis (cache)
- **Storage**: MinIO (S3-compatible object storage)
- **Computing**: Ray (distributed computing framework)
- **Containerization**: Docker with multi-stage builds

### Infrastructure
- **Orchestration**: Docker Compose (dev), Kubernetes (prod)
- **CI/CD**: GitHub Actions with multi-environment support
- **Monitoring**: Prometheus + Grafana
- **Security**: TLS/SSL, secret management, vulnerability scanning
- **Scaling**: Horizontal pod autoscaling, load balancing

## Service Architecture

### Frontend Service (Port 9000)
```typescript
// Service Responsibilities:
- User interface and experience
- Client-side AI flows with Genkit
- Real-time data visualization
- Authentication and session management
- API communication with backend services

// Key Components:
- Dashboard layout with sidebar navigation
- AI-powered contextual help system
- Responsive grid system for data display
- Form handling with validation
- WebSocket connections for real-time updates
```

### API Gateway (Port 8000)
```python
# Service Responsibilities:
- Request routing and load balancing
- Authentication and authorization
- Rate limiting and request validation
- API versioning and documentation
- Cross-cutting concerns (logging, metrics)

# Key Features:
- JWT token validation
- Request/response transformation
- Service discovery integration
- Health check aggregation
- OpenAPI documentation generation
```

### Data Service (Port 8001)
```python
# Service Responsibilities:
- Data ingestion and processing
- Database operations (CRUD)
- Data validation and transformation
- Batch processing workflows
- Data export and reporting

# Key Components:
- PostgreSQL ORM with SQLAlchemy
- Redis caching layer
- Data pipeline orchestration
- Background task processing
- Data quality monitoring
```

### AI Service (Port 8002)
```python
# Service Responsibilities:
- Machine learning model inference
- AI-powered data analysis
- Natural language processing
- Predictive analytics
- Model training and evaluation

# Key Components:
- Ray distributed computing integration
- Model versioning and deployment
- Feature engineering pipelines
- Real-time inference endpoints
- Model monitoring and drift detection
```

### Backend Pro2 (Port 8100-8199)
```python
# Service Responsibilities:
- Secondary project isolation
- Experimental features
- A/B testing environments
- Independent scaling
- Feature flag management

# Isolation Benefits:
- Independent deployment cycles
- Resource allocation control
- Risk mitigation for new features
- Development team separation
- Performance testing isolation
```

## Data Architecture

### Database Schema
```sql
-- Core Entities
Users (id, email, created_at, updated_at)
Projects (id, name, user_id, config, status)
Analytics (id, project_id, metrics, timestamp)
AI_Models (id, name, version, config, status)

-- Relationships
user_projects (user_id, project_id, role)
project_analytics (project_id, analytics_id)
model_deployments (model_id, project_id, status)
```

### Data Flow
```
┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   Frontend   │───▶│ API Gateway │───▶│ Data Service │
│  (User Input)│    │(Validation) │    │ (Processing) │
└──────────────┘    └─────────────┘    └──────┬───────┘
                                              │
┌──────────────┐    ┌─────────────┐           │
│  AI Service  │◀───│    Redis    │◀──────────┘
│ (Analysis)   │    │  (Cache)    │
└──────┬───────┘    └─────────────┘
       │
       ▼
┌──────────────┐    ┌─────────────┐
│ PostgreSQL   │    │    MinIO    │
│ (Persistence)│    │ (File Store)│
└──────────────┘    └─────────────┘
```

## Security Architecture

### Authentication Flow
```
1. User Login → Frontend
2. Frontend → API Gateway (credentials)
3. API Gateway → Auth Service (validation)
4. Auth Service → Database (user verification)
5. Database → Auth Service (user data)
6. Auth Service → API Gateway (JWT token)
7. API Gateway → Frontend (authenticated session)
8. Frontend stores JWT for subsequent requests
```

### Security Layers
- **Network**: HTTPS/TLS encryption, firewall rules
- **Application**: JWT tokens, RBAC, input validation
- **Database**: Connection encryption, row-level security
- **Infrastructure**: Container security, secret management
- **Monitoring**: Security event logging, anomaly detection

## Scalability Design

### Horizontal Scaling
- **Frontend**: CDN distribution, edge caching
- **API Gateway**: Load balancer with multiple instances
- **Microservices**: Independent scaling per service
- **Database**: Read replicas, connection pooling
- **Storage**: Distributed object storage

### Performance Optimization
- **Caching Strategy**: Redis for session/API responses
- **Database Optimization**: Indexes, query optimization
- **Frontend Optimization**: Code splitting, lazy loading
- **API Optimization**: Response compression, pagination
- **Resource Management**: CPU/memory limits, auto-scaling

## Deployment Architecture

### Development Environment
```yaml
# docker-compose.dev.yml
services:
  frontend:
    ports: ["9000:9000"]
    environment: development
  
  api-gateway:
    ports: ["8000:8000"]
    depends_on: [postgres, redis]
  
  data-service:
    ports: ["8001:8001"]
    volumes: [./data:/app/data]
```

### Production Environment
```yaml
# kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: saas-control-deck
spec:
  replicas: 3
  selector:
    matchLabels:
      app: saas-control-deck
  template:
    spec:
      containers:
      - name: frontend
        image: saascontrol/frontend:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Monitoring and Observability

### Metrics Collection
- **Application Metrics**: Response times, error rates, throughput
- **Infrastructure Metrics**: CPU, memory, disk, network
- **Business Metrics**: User activity, feature usage
- **Security Metrics**: Failed logins, suspicious activity

### Logging Strategy
- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: ERROR, WARN, INFO, DEBUG
- **Log Aggregation**: Centralized logging with ELK stack
- **Retention**: 30 days for application logs, 90 days for audit logs

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "database": await check_database(),
            "redis": await check_redis(),
            "ai_service": await check_ai_service()
        }
    }
```

## Disaster Recovery

### Backup Strategy
- **Database**: Daily full backups, hourly incremental
- **File Storage**: Cross-region replication
- **Configuration**: Version-controlled infrastructure as code
- **Application State**: Redis persistence enabled

### Recovery Procedures
- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 1 hour
- **Failover Process**: Automated with health check triggers
- **Data Validation**: Integrity checks post-recovery

---

This architecture supports the platform's 6-day development cycles while maintaining enterprise-grade reliability, security, and scalability.