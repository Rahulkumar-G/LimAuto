# LimAuto Setup Guide

## Issues Fixed

### 1. Frontend TypeScript Compatibility
- **Issue**: React Scripts 5.0.1 incompatible with TypeScript 5.4.2
- **Fix**: Downgraded TypeScript to ^4.9.5 for compatibility
- **Location**: `frontend/package.json`

### 2. Backend CORS Configuration
- **Issue**: Frontend couldn't connect to backend due to CORS restrictions
- **Fix**: Added Flask-CORS configuration to backend API
- **Location**: `BookLLM/src/api.py`

### 3. Service Management
- **Issue**: No clear way to start backend and frontend services
- **Fix**: Created startup scripts:
  - `start_backend.py` - Backend Flask server
  - `start_frontend.py` - Frontend React server  
  - `start_dev.py` - Both services simultaneously

### 4. Docker Configuration
- **Issue**: No containerization support
- **Fix**: Complete Docker setup:
  - `Dockerfile` - Multi-stage build
  - `docker-compose.yml` - Production setup
  - `docker-compose.dev.yml` - Development setup
  - `docker-start.sh` - Easy management script

## How to Start the Application

### Option 1: Local Development
```bash
# Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Start both services
python start_dev.py

# Or start separately:
python start_backend.py  # Terminal 1
python start_frontend.py # Terminal 2
```

### Option 2: Docker (Recommended)
```bash
# Development mode (with live reload)
./docker-start.sh dev

# Production mode  
./docker-start.sh prod

# Stop services
./docker-start.sh stop
```

## Service URLs

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000  
- **Health Check**: http://localhost:8000/health
- **API Documentation**: See README.md for endpoint details

## Troubleshooting

### Backend Won't Start
- Check Python dependencies: `pip install -r requirements.txt`
- Verify configuration: `BookLLM/config.yaml`
- Check port 8000 availability: `lsof -i :8000`

### Frontend Won't Start  
- Check Node dependencies: `cd frontend && npm install`
- Verify TypeScript version: `npm list typescript`
- Check port 3000 availability: `lsof -i :3000`

### Docker Issues
- Ensure Docker is running: `docker info`
- Check Docker Compose: `docker-compose --version`
- View logs: `docker-compose logs -f`

## Development Workflow

1. **Start Services**: Use `python start_dev.py` or `./docker-start.sh dev`
2. **Backend Changes**: Auto-reload enabled in development mode
3. **Frontend Changes**: Hot reload available with React dev server
4. **Test APIs**: Use `curl` or frontend UI to test endpoints
5. **Monitor Health**: Check `/health` endpoint regularly

## Production Deployment

1. **Docker Production**: `./docker-start.sh prod`
2. **Services Included**:
   - Nginx reverse proxy
   - Redis for caching
   - Backend API server
   - Static frontend files
3. **Access**: http://localhost (port 80)

## Next Steps

- Configure your LLM provider in `BookLLM/config.yaml`
- Set up Ollama or OpenAI API keys
- Test book generation with the frontend interface
- Monitor logs and metrics for production use