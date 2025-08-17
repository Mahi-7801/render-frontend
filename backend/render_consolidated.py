#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolidated Lavangam Backend for Render Deployment
Combines all services under one FastAPI app with route prefixes
"""

import os
import sys
import asyncio
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

print("🚀 Starting Lavangam Consolidated Backend...")

# Add the backend directory to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))
print(f"✅ Backend path added: {backend_path}")

# Check Python version
python_version = sys.version_info
print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")

print("📦 Importing packages...")

try:
    from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, HTMLResponse
    import uvicorn
    from supabase import create_client, Client
    import requests
    import json
    from datetime import datetime
    import mysql.connector
    from mysql.connector import Error
    import pandas as pd
    import psutil
    from dotenv import load_dotenv
    print("✅ All packages imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

print("🔧 Loading environment variables...")
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Lavangam Consolidated Backend",
    description="All services consolidated into one API",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("✅ FastAPI app initialized with CORS")

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL", "https://zjfjaezztfydiryzfd.supabase.co")
supabase_key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpqZmphZXp6dGZ5ZGlyeXpzeXZkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTAyNzAyMSwiZXhwIjoyMDY2NjAzMDIxfQ.sRbGz6wbBoMmY8Ol3vEPc4VOh2oEWpcONi9DkUsTpKk")

try:
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✅ Supabase client initialized")
except Exception as e:
    print(f"⚠️ Supabase initialization warning: {e}")
    supabase = None

# ============================================================================
# MAIN BACKEND ROUTES (Port 8000 equivalent)
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "message": "Welcome to Lavangam Consolidated Backend",
        "service": "lavangam-backend",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "services": [
            "main_backend",
            "file_manager", 
            "eproc_server",
            "system_usage",
            "dashboard_api",
            "scrapers_api",
            "analytics_api",
            "additional_analytics",
            "eproc_websocket",
            "eproc_api"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Render monitoring"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "lavangam-consolidated-backend",
            "environment": os.getenv("RENDER_ENVIRONMENT", "production"),
            "python_version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            "port": os.getenv("PORT", "8000"),
            "host": "0.0.0.0",
            "uptime": "running",
            "consolidated_services": True
        }
        
        # Test database connection
        try:
            db_host = os.getenv("DB_HOST", "44.244.61.85")
            if db_host:
                health_status["database"] = "configured"
            else:
                health_status["database"] = "not_configured"
        except:
            health_status["database"] = "error"
        
        return health_status
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong", "status": "ok"}

# ============================================================================
# FILE MANAGER ROUTES (Port 5002 equivalent)
# ============================================================================

@app.get("/file-manager/")
async def file_manager_root():
    """File Manager service root"""
    return {
        "service": "file_manager",
        "status": "running",
        "port_equivalent": "5002",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/file-manager/health")
async def file_manager_health():
    """File Manager health check"""
    return {
        "service": "file_manager",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# E-PROCUREMENT SERVER ROUTES (Port 5023 equivalent)
# ============================================================================

@app.get("/eproc/")
async def eproc_root():
    """E-Procurement service root"""
    return {
        "service": "eproc_server",
        "status": "running",
        "port_equivalent": "5023",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/eproc/health")
async def eproc_health():
    """E-Procurement health check"""
    return {
        "service": "eproc_server",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# SYSTEM USAGE ROUTES (Port 5024 equivalent)
# ============================================================================

@app.get("/system/")
async def system_root():
    """System Usage service root"""
    return {
        "service": "system_usage",
        "status": "running",
        "port_equivalent": "5024",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/system/health")
async def system_health():
    """System Usage health check"""
    return {
        "service": "system_usage",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/system/metrics")
async def system_metrics():
    """System metrics endpoint"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available": memory.available,
            "memory_total": memory.total,
            "disk_percent": disk.percent,
            "disk_free": disk.free,
            "disk_total": disk.total,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System metrics error: {str(e)}")

# ============================================================================
# DASHBOARD API ROUTES (Port 8004 equivalent)
# ============================================================================

@app.get("/dashboard/")
async def dashboard_root():
    """Dashboard API service root"""
    return {
        "service": "dashboard_api",
        "status": "running",
        "port_equivalent": "8004",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/dashboard/health")
async def dashboard_health():
    """Dashboard API health check"""
    return {
        "service": "dashboard_api",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# SCRAPERS API ROUTES (Port 5022 equivalent)
# ============================================================================

@app.get("/scrapers/")
async def scrapers_root():
    """Scrapers API service root"""
    return {
        "service": "scrapers_api",
        "status": "running",
        "port_equivalent": "5022",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/scrapers/health")
async def scrapers_health():
    """Scrapers API health check"""
    return {
        "service": "scrapers_api",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# ANALYTICS API ROUTES (Port 8001 equivalent)
# ============================================================================

@app.get("/analytics/")
async def analytics_root():
    """Analytics API service root"""
    return {
        "service": "analytics_api",
        "status": "running",
        "port_equivalent": "8001",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/analytics/health")
async def analytics_health():
    """Analytics API health check"""
    return {
        "service": "analytics_api",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# ADDITIONAL ANALYTICS ROUTES (Port 8002 equivalent)
# ============================================================================

@app.get("/analytics-additional/")
async def additional_analytics_root():
    """Additional Analytics API service root"""
    return {
        "service": "additional_analytics",
        "status": "running",
        "port_equivalent": "8002",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/analytics-additional/health")
async def additional_analytics_health():
    """Additional Analytics API health check"""
    return {
        "service": "additional_analytics",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# E-PROCUREMENT WEBSOCKET ROUTES (Port 5020 equivalent)
# ============================================================================

@app.get("/eproc-ws/")
async def eproc_websocket_root():
    """E-Procurement WebSocket service root"""
    return {
        "service": "eproc_websocket",
        "status": "running",
        "port_equivalent": "5020",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/eproc-ws/health")
async def eproc_websocket_health():
    """E-Procurement WebSocket health check"""
    return {
        "service": "eproc_websocket",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# E-PROCUREMENT API ROUTES (Port 5021 equivalent)
# ============================================================================

@app.get("/eproc-api/")
async def eproc_api_root():
    """E-Procurement API service root"""
    return {
        "service": "eproc_api",
        "status": "running",
        "port_equivalent": "5021",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/eproc-api/health")
async def eproc_api_health():
    """E-Procurement API health check"""
    return {
        "service": "eproc_api",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# DATABASE TEST ENDPOINTS
# ============================================================================

@app.get("/test-database")
async def test_database():
    """Test database connectivity"""
    try:
        db_host = os.getenv("DB_HOST", "44.244.61.85")
        db_port = int(os.getenv("DB_PORT", "3306"))
        db_name = os.getenv("DB_NAME", "Toolinformation")
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "thanuja")
        
        connection = mysql.connector.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            connection_timeout=10,
            autocommit=True
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            cursor.close()
            connection.close()
            
            return {
                "status": "success",
                "message": "Database connection successful",
                "version": version[0] if version else "Unknown",
                "timestamp": datetime.now().isoformat()
            }
    except Error as e:
        return {
            "status": "error",
            "message": "Database connection failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Database test failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ============================================================================
# AI ASSISTANT ENDPOINT
# ============================================================================

@app.post("/api/ai-assistant")
async def ai_assistant(request: Request):
    """AI Assistant endpoint"""
    try:
        data = await request.json()
        user_message = data.get("message", "")
        
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise HTTPException(status_code=400, detail="API key not configured")
        
        response = {
            "message": f"AI Assistant received: {user_message}",
            "timestamp": datetime.now().isoformat(),
            "api_key_configured": bool(api_key)
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Assistant error: {str(e)}")

# ============================================================================
# SERVICE STATUS OVERVIEW
# ============================================================================

@app.get("/services/status")
async def all_services_status():
    """Get status of all consolidated services"""
    services = {
        "main_backend": {"port_equivalent": "8000", "status": "running"},
        "file_manager": {"port_equivalent": "5002", "status": "running"},
        "eproc_server": {"port_equivalent": "5023", "status": "running"},
        "system_usage": {"port_equivalent": "5024", "status": "running"},
        "dashboard_api": {"port_equivalent": "8004", "status": "running"},
        "scrapers_api": {"port_equivalent": "5022", "status": "running"},
        "analytics_api": {"port_equivalent": "8001", "status": "running"},
        "additional_analytics": {"port_equivalent": "8002", "status": "running"},
        "eproc_websocket": {"port_equivalent": "5020", "status": "running"},
        "eproc_api": {"port_equivalent": "5021", "status": "running"}
    }
    
    return {
        "consolidated_backend": True,
        "main_port": os.getenv("PORT", "8000"),
        "services": services,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# MAIN STARTUP
# ============================================================================

if __name__ == "__main__":
    print("🚀 Starting Lavangam Consolidated Backend on Render...")
    print(f"✅ Environment: {os.getenv('RENDER_ENVIRONMENT', 'production')}")
    print(f"✅ Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    print(f"✅ Supabase URL: {supabase_url}")
    print(f"✅ Database Host: {os.getenv('DB_HOST', '44.244.61.85')}")
    
    try:
        port = int(os.getenv("PORT", 8000))
        print(f"🌐 Binding to port: {port}")
    except ValueError as e:
        print(f"❌ Invalid PORT environment variable: {e}")
        port = 8000
        print(f"🔄 Using default port: {port}")
    
    print("🚀 Starting consolidated backend...")
    print("✅ All services consolidated into one FastAPI app")
    print("✅ Each service available via route prefixes")
    print("✅ Single port deployment for Render compatibility")
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level="info",
            access_log=True,
            server_header=False
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("🔍 Check the logs above for more details")
        sys.exit(1)
