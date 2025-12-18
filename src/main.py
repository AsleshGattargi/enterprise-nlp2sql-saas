from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi import status as status_module
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from sqlalchemy import text
import uvicorn
import logging
import uuid
import time
import json
import pandas as pd
import io
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.models import (
    LoginRequest, LoginResponse, QueryRequest, QueryResponse,
    UserResponse, OrganizationResponse, HDTResponse, AgentResponse
)
from src.auth import auth_manager, get_current_user, get_admin_user
from src.database import db_manager
from src.hdt_manager import hdt_manager
from src.nlp2sql_engine import nlp2sql_engine
from src.security import security_manager

# Import database cloning components
from src.cloning_api import setup_cloning_routes

# Import RBAC components
from src.tenant_rbac_manager import TenantRBACManager
from src.jwt_middleware import setup_jwt_middleware, RBACDependencies
from src.cross_tenant_user_manager import CrossTenantUserManager
from src.rbac_api import setup_rbac_routes

# Import dynamic routing components
from src.tenant_connection_manager import TenantConnectionManager
from src.tenant_routing_middleware import setup_tenant_routing_middleware
from src.tenant_aware_nlp2sql import TenantAwareNLP2SQL
from src.performance_optimization import PerformanceOptimizer
from src.error_handling_monitoring import setup_monitoring_system
from src.dynamic_api_endpoints import setup_dynamic_api_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize RBAC system
RBAC_DB_CONFIG = {
    "type": "mysql",
    "connection": {
        "host": "localhost",
        "port": 3306,
        "database": "rbac_central",
        "user": "rbac_user",
        "password": "rbac_password",
        "charset": "utf8mb4"
    }
}

JWT_SECRET = "your-super-secret-jwt-key-change-in-production"
rbac_manager = TenantRBACManager(RBAC_DB_CONFIG, JWT_SECRET)
cross_tenant_manager = CrossTenantUserManager(rbac_manager)

# Initialize dynamic routing components
connection_manager = TenantConnectionManager(database_cloner)
nlp2sql_engine = TenantAwareNLP2SQL(connection_manager)
performance_optimizer = PerformanceOptimizer(connection_manager)
monitoring_system = setup_monitoring_system(connection_manager)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Multi-Tenant NLP2SQL API")

    # Initialize RBAC role templates
    try:
        results = rbac_manager.role_manager.install_default_templates()
        logger.info(f"RBAC role templates initialized: {results}")
    except Exception as e:
        logger.error(f"Failed to initialize RBAC templates: {e}")

    # Start monitoring system
    try:
        await monitoring_system.start_monitoring()
        logger.info("Monitoring system started")
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")

    yield
    logger.info("Shutting down Multi-Tenant NLP2SQL API")

    # Stop monitoring system
    try:
        await monitoring_system.stop_monitoring()
        logger.info("Monitoring system stopped")
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")

    db_manager.close_connections()

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Tenant NLP2SQL API",
    description="A multi-tenant AI service for natural language to SQL conversion with Human Digital Twins",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],  # Streamlit and React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup JWT middleware and RBAC dependencies
rbac_deps = setup_jwt_middleware(
    app,
    rbac_manager,
    exclude_paths=[
        "/", "/health", "/docs", "/redoc", "/openapi.json",
        "/api/v1/auth/login", "/api/v1/auth/register",
        "/api/v1/cloning/system/status"
    ]
)

# Setup tenant routing middleware
switch_manager = setup_tenant_routing_middleware(
    app,
    connection_manager,
    rbac_manager,
    exclude_paths=[
        "/", "/health", "/docs", "/redoc", "/openapi.json",
        "/api/v1/auth/login", "/api/v1/auth/register",
        "/api/v1/cloning/system/status",
        "/api/v1/rbac/system/status"
    ]
)

security = HTTPBearer()

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Multi-Tenant NLP2SQL API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test metadata database connection
        with db_manager.get_metadata_db() as db:
            db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "metadata_db": "connected",
                "nlp2sql_engine": "active",
                "security_manager": "active",
                "hdt_manager": "active"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request):
    """User authentication endpoint"""
    client_ip = get_client_ip(req)
    
    try:
        # Check rate limiting
        rate_check = security_manager.check_rate_limit("anonymous", client_ip)
        if rate_check['rate_limited']:
            raise HTTPException(
                status_code=status_module.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
        
        # Authenticate user
        auth_result = auth_manager.authenticate_user(request.email, request.password)
        
        logger.info(f"Successful login for user {request.email} from IP {client_ip}")
        
        return LoginResponse(**auth_result)
        
    except HTTPException:
        logger.warning(f"Failed login attempt for {request.email} from IP {client_ip}")
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        user_id=current_user["user_id"],
        org_id=current_user["org_id"],
        username=current_user.get("username", ""),
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        department=current_user.get("department"),
        role=current_user["role"],
        is_active=True
    )

@app.get("/user/hdt", response_model=HDTResponse)
async def get_user_hdt(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user's Human Digital Twin profile"""
    try:
        hdt_info = hdt_manager.get_user_hdt(current_user["user_id"])
        
        if not hdt_info:
            raise HTTPException(
                status_code=status_module.HTTP_404_NOT_FOUND,
                detail="HDT profile not found for user"
            )
        
        return HDTResponse(
            hdt_id=hdt_info["hdt_id"],
            name=hdt_info["name"],
            description=hdt_info["description"],
            context=hdt_info["context"],
            skillset=hdt_info["skillset"],
            languages=hdt_info["languages"],
            agents=[agent["agent_type"] for agent in hdt_info["agents"]]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting HDT for user {current_user['user_id']}: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving HDT profile"
        )

@app.get("/user/agents")
async def get_user_agents(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get available agents for user's HDT"""
    try:
        hdt_info = hdt_manager.get_user_hdt(current_user["user_id"])
        
        if not hdt_info:
            return {"agents": []}
        
        agents = hdt_manager.get_available_agents(hdt_info["hdt_id"])
        
        return {
            "user_id": current_user["user_id"],
            "hdt_id": hdt_info["hdt_id"],
            "agents": agents
        }
        
    except Exception as e:
        logger.error(f"Error getting agents for user {current_user['user_id']}: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving available agents"
        )

@app.post("/query/execute", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    req: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Execute natural language query"""
    client_ip = get_client_ip(req)
    query_id = str(uuid.uuid4())
    start_time = time.time()
    
    print(f"[API_DEBUG] Starting query execution: {request.query_text}")
    logger.info(f"Starting query execution: query_id={query_id}, user={current_user['user_id']}, query='{request.query_text}'")
    
    try:
        # Comprehensive security check
        security_check = security_manager.comprehensive_security_check(
            request.query_text,
            current_user["user_id"],
            current_user["role"],
            current_user["org_id"],
            client_ip
        )
        
        if not security_check['passed']:
            # Log blocked query
            await log_query(
                query_id, current_user, request.query_text, None,
                'blocked', 0, '; '.join(security_check['errors'])
            )
            
            raise HTTPException(
                status_code=status_module.HTTP_403_FORBIDDEN,
                detail=f"Query blocked: {'; '.join(security_check['errors'])}"
            )
        
        # Get organization database info
        with db_manager.get_metadata_db() as db:
            from src.models import Organization
            org = db.query(Organization).filter(
                Organization.org_id == current_user["org_id"]
            ).first()
            
            if not org:
                raise HTTPException(
                    status_code=status_module.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )
        
        # Process query with NLP2SQL engine
        logger.info(f"Processing query: '{request.query_text}' for user {current_user['user_id']}")
        query_result = nlp2sql_engine.process_query(
            request.query_text,
            current_user["user_id"],
            current_user["org_id"],
            org.database_type,
            org.database_name
        )
        logger.info(f"Query result: {query_result}")
        
        if not query_result['success']:
            # Determine if this is a permission/security issue or a processing error
            is_blocked = query_result.get('blocked', False)
            status = 'blocked' if is_blocked else 'error'
            
            await log_query(
                query_id, current_user, request.query_text, None,
                status, int((time.time() - start_time) * 1000),
                query_result.get('error', 'Unknown error')
            )
            
            return QueryResponse(
                query_id=query_id,
                generated_sql=None,
                results=[],
                execution_time_ms=int((time.time() - start_time) * 1000),
                status=status,
                message=query_result.get('error', 'Query processing failed'),
                export_url=None
            )
        
        generated_sql = query_result['generated_sql']
        
        # Execute query on organization database
        db_result = db_manager.execute_query(
            current_user["org_id"],
            org.database_type,
            org.database_name,
            generated_sql
        )
        
        if not db_result['success']:
            await log_query(
                query_id, current_user, request.query_text, generated_sql,
                'error', int((time.time() - start_time) * 1000),
                db_result.get('error', 'Query execution failed')
            )
            
            return QueryResponse(
                query_id=query_id,
                generated_sql=generated_sql,
                results=[],
                execution_time_ms=int((time.time() - start_time) * 1000),
                status='error',
                message=db_result.get('error', 'Query execution failed'),
                export_url=None
            )
        
        # Sanitize results based on user role
        sanitized_results = security_manager.sanitize_query_output(
            db_result['data'], current_user["role"]
        )
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # Log successful query
        await log_query(
            query_id, current_user, request.query_text, generated_sql,
            'success', execution_time, None
        )
        
        # Handle export if requested
        export_url = None
        if request.export_format:
            export_url = await handle_export(
                sanitized_results, request.export_format, query_id
            )
        
        return QueryResponse(
            query_id=query_id,
            generated_sql=generated_sql,
            results=sanitized_results,
            execution_time_ms=execution_time,
            status='success',
            message=f"Query executed successfully. Returned {len(sanitized_results)} rows.",
            export_url=export_url
        )
        
    except HTTPException:
        raise
    except PermissionError as e:
        # Handle permission errors with user-friendly messages
        logger.warning(f"Permission denied for user {current_user['user_id']}: {e}")
        
        await log_query(
            query_id, current_user, request.query_text, None,
            'blocked', int((time.time() - start_time) * 1000), str(e)
        )
        
        return QueryResponse(
            query_id=query_id,
            generated_sql=None,
            results=[],
            execution_time_ms=int((time.time() - start_time) * 1000),
            status='blocked',
            message=str(e),  # Use the user-friendly permission error message
            export_url=None
        )
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        await log_query(
            query_id, current_user, request.query_text, None,
            'error', int((time.time() - start_time) * 1000), str(e)
        )
        
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Query execution failed"
        )

@app.get("/query/suggestions")
async def get_query_suggestions(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get query suggestions based on user's organization and HDT"""
    try:
        # Get organization info
        with db_manager.get_metadata_db() as db:
            from src.models import Organization
            org = db.query(Organization).filter(
                Organization.org_id == current_user["org_id"]
            ).first()
        
        # Get HDT context
        hdt_info = hdt_manager.get_user_hdt(current_user["user_id"])
        
        # Generate suggestions based on database type and HDT
        suggestions = []
        
        if org.database_type == 'postgresql' and 'techcorp' in org.database_name:
            suggestions.extend([
                "Show me all products",
                "How many products do we have?",
                "List sales from last month",
                "What's the average product price?",
                "Show inventory levels by warehouse"
            ])
        elif org.database_type == 'mysql' and 'healthplus' in org.database_name:
            suggestions.extend([
                "Show me all patients",
                "How many appointments today?",
                "List pending bills",
                "Show treatments by doctor",
                "What's the average treatment cost?"
            ])
        elif org.database_type == 'mongodb' and 'retailmax' in org.database_name:
            suggestions.extend([
                "Show me all products",
                "How many sales this month?",
                "List top customers",
                "Show inventory by store",
                "What are the most popular categories?"
            ])
        
        # Add HDT-specific suggestions
        if hdt_info and 'analyst' in hdt_info.get('name', '').lower():
            suggestions.extend([
                "Analyze sales trends over time",
                "Compare performance by category",
                "Show correlation between price and sales"
            ])
        
        return {
            "suggestions": suggestions,
            "database_type": org.database_type,
            "organization": org.org_name,
            "hdt_profile": hdt_info.get('name') if hdt_info else None
        }
        
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        return {"suggestions": [], "error": str(e)}

@app.get("/admin/users", dependencies=[Depends(get_admin_user)])
async def get_organization_users(current_user: Dict[str, Any] = Depends(get_admin_user)):
    """Get all users in the organization (admin only)"""
    try:
        with db_manager.get_metadata_db() as db:
            from src.models import User
            users = db.query(User).filter(
                User.org_id == current_user["org_id"]
            ).all()
            
            return {
                "users": [
                    {
                        "user_id": user.user_id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                        "department": user.department,
                        "role": user.role,
                        "is_active": user.is_active
                    }
                    for user in users
                ]
            }
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )

@app.get("/admin/query-logs", dependencies=[Depends(get_admin_user)])
async def get_query_logs(
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """Get query logs for the organization (admin only)"""
    try:
        with db_manager.get_metadata_db() as db:
            from src.models import QueryLog, User
            
            logs = db.query(QueryLog, User.username).join(
                User, QueryLog.user_id == User.user_id
            ).filter(
                QueryLog.org_id == current_user["org_id"]
            ).order_by(
                QueryLog.timestamp.desc()
            ).limit(limit).all()
            
            return {
                "logs": [
                    {
                        "log_id": log.QueryLog.log_id,
                        "user_id": log.QueryLog.user_id,
                        "username": log.username,
                        "query_text": log.QueryLog.query_text,
                        "generated_sql": log.QueryLog.generated_sql,
                        "execution_status": log.QueryLog.execution_status,
                        "execution_time_ms": log.QueryLog.execution_time_ms,
                        "error_message": log.QueryLog.error_message,
                        "timestamp": log.QueryLog.timestamp.isoformat()
                    }
                    for log in logs
                ]
            }
    except Exception as e:
        logger.error(f"Error getting query logs: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving query logs"
        )

async def log_query(
    query_id: str, user: Dict[str, Any], query_text: str,
    generated_sql: Optional[str], status: str, execution_time: int,
    error_message: Optional[str]
):
    """Log query execution"""
    try:
        with db_manager.get_metadata_db() as db:
            from src.models import QueryLog
            
            log_entry = QueryLog(
                log_id=query_id,
                org_id=user["org_id"],
                user_id=user["user_id"],
                query_text=query_text,
                generated_sql=generated_sql,
                query_type="nlp2sql",
                execution_status=status,
                execution_time_ms=execution_time,
                error_message=error_message,
                timestamp=datetime.utcnow()
            )
            
            db.add(log_entry)
            db.commit()
            
    except Exception as e:
        logger.error(f"Error logging query: {e}")

async def handle_export(data: List[Dict[str, Any]], format: str, query_id: str) -> str:
    """Handle data export in various formats"""
    try:
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        if format.lower() == 'csv':
            filename = f"export_{query_id}.csv"
            df.to_csv(f"exports/{filename}", index=False)
            return f"/exports/{filename}"
        
        elif format.lower() == 'excel':
            filename = f"export_{query_id}.xlsx"
            df.to_excel(f"exports/{filename}", index=False)
            return f"/exports/{filename}"
        
        elif format.lower() == 'json':
            filename = f"export_{query_id}.json"
            df.to_json(f"exports/{filename}", orient='records', indent=2)
            return f"/exports/{filename}"
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        return None

# Setup database cloning routes
setup_cloning_routes(app)

# Setup RBAC routes
setup_rbac_routes(app, rbac_manager, cross_tenant_manager, rbac_deps)

# Setup dynamic API routes
setup_dynamic_api_routes(app, connection_manager, nlp2sql_engine, switch_manager, rbac_deps)

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )