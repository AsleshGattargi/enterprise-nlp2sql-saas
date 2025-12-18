# Enhanced RBAC Layer Integration

## Multi-Tenant NLP2SQL System with Complete Role-Based Access Control

A comprehensive Role-Based Access Control (RBAC) system integrated with the Multi-Tenant NLP2SQL platform, providing enterprise-grade security, tenant isolation, and user management capabilities.

## 🌟 Key Features

- **Central RBAC Database**: Separate metadata database for complete tenant isolation
- **Hierarchical Role System**: Built-in roles with inheritance and custom role support
- **Cross-Tenant User Management**: Users can access multiple tenants with different roles
- **JWT-Based Authentication**: Secure token-based authentication with tenant context
- **Permission-Based Authorization**: Granular permissions for resources and actions
- **Session Management**: Complete session lifecycle with automatic cleanup
- **Audit Logging**: Comprehensive audit trail for all RBAC operations
- **API Integration**: RESTful endpoints for all RBAC operations
- **Performance Optimized**: Efficient permission checking and caching

## 🏗️ Architecture Overview

```
Enhanced RBAC System
├── Central RBAC Database (MySQL/PostgreSQL/SQLite)
│   ├── master_users (Global user registry)
│   ├── master_organizations (Tenant registry)
│   ├── role_templates (System-wide roles)
│   ├── user_tenant_mappings (Cross-tenant access)
│   ├── user_tenant_roles (Role assignments)
│   ├── tenant_access_sessions (JWT sessions)
│   ├── tenant_access_requests (Approval workflow)
│   └── rbac_audit_log (Complete audit trail)
├── TenantRBACManager (Core RBAC engine)
├── RoleTemplateManager (Role and permission system)
├── CrossTenantUserManager (Multi-tenant user management)
├── JWT Middleware (Authentication and authorization)
└── RBAC API (RESTful endpoints)
```

## 📦 Components

### 1. Central RBAC Database Schema
**File**: `rbac_schemas/rbac_central_database.sql`

The heart of the RBAC system - a separate database that manages:
- **master_users**: Global user registry with authentication credentials
- **master_organizations**: Links to cloned tenant databases
- **role_templates**: System-wide role definitions with JSON permissions
- **user_tenant_mappings**: Cross-tenant access mappings
- **user_tenant_roles**: Role assignments per tenant
- **tenant_access_sessions**: JWT session tracking per tenant
- **tenant_access_requests**: Access request approval workflow
- **bulk_operations**: Bulk operation tracking
- **rbac_audit_log**: Complete RBAC operation auditing

**Key Features**:
- UUID primary keys for security
- JSON columns for flexible permissions
- Comprehensive indexing for performance
- Foreign key constraints for data integrity
- Audit triggers for change tracking

### 2. Role Template System
**File**: `src/rbac_role_templates.py`

Manages hierarchical role definitions with inheritance:

```python
# Built-in Role Templates
role_templates = {
    "super_admin": "Global system administrator",
    "admin": "Tenant administrator",
    "analyst": "Data analyst with query capabilities",
    "business_user": "Business user with limited access",
    "viewer": "Read-only report viewer",
    "api_user": "Programmatic API access",
    "guest": "Temporary demonstration access"
}
```

**Features**:
- Permission inheritance
- Condition-based permissions
- Custom role creation
- Role hierarchy validation
- Permission resolution with caching

### 3. TenantRBACManager
**File**: `src/tenant_rbac_manager.py`

Core RBAC engine providing:

```python
class TenantRBACManager:
    def create_user(username, email, password, full_name, is_global_admin)
    def authenticate_user(username_or_email, password)
    def grant_tenant_access(user_id, tenant_id, role_names, granted_by)
    def create_tenant_session(user_id, tenant_id, ip_address, user_agent)
    def generate_jwt_token(tenant_session)
    def validate_jwt_token(token)
    def check_user_permission(user_id, tenant_id, resource, level, conditions)
```

**Features**:
- Secure password hashing (PBKDF2)
- JWT token generation and validation
- Session lifecycle management
- Permission checking with conditions
- Audit logging for all operations

### 4. Cross-Tenant User Management
**File**: `src/cross_tenant_user_manager.py`

Advanced user management across multiple tenants:

```python
class CrossTenantUserManager:
    def request_tenant_access(user_id, tenant_id, requested_roles, justification)
    def approve_access_request(request_id, reviewed_by)
    def get_cross_tenant_user_summary(user_id)
    def initiate_bulk_operation(operation_type, user_ids, tenant_ids, parameters)
    def generate_user_access_report(user_id)
```

**Features**:
- Access request workflow
- Bulk operations for user management
- Cross-tenant access summaries
- Comprehensive user access reports
- Automated cleanup operations

### 5. JWT Middleware
**File**: `src/jwt_middleware.py`

FastAPI middleware for authentication and authorization:

```python
class JWTMiddleware:
    # Automatic JWT validation
    # Tenant context injection
    # Permission-based route protection
    # Request/response logging

class RBACDependencies:
    def require_permission(resource, level, conditions)
    def require_role(*required_roles)
    def require_global_admin()
```

**Features**:
- Automatic JWT validation
- Tenant context injection into request state
- Permission-based dependencies
- Role-based dependencies
- Configurable excluded paths

### 6. RBAC API Endpoints
**File**: `src/rbac_api.py`

Comprehensive REST API for RBAC operations:

#### Authentication
- `POST /api/v1/rbac/auth/login` - User authentication with tenant context
- `POST /api/v1/rbac/auth/switch-tenant` - Switch tenant context

#### User Management
- `POST /api/v1/rbac/users` - Create new user (Global admin only)
- `GET /api/v1/rbac/users/me` - Get current user profile
- `GET /api/v1/rbac/users/{user_id}/report` - User access report

#### Tenant Access Management
- `POST /api/v1/rbac/access/grant` - Grant tenant access
- `POST /api/v1/rbac/access/revoke` - Revoke tenant access
- `POST /api/v1/rbac/access/request` - Request tenant access
- `POST /api/v1/rbac/access/requests/{request_id}/approve` - Approve request
- `POST /api/v1/rbac/access/requests/{request_id}/reject` - Reject request

#### Permission Management
- `POST /api/v1/rbac/permissions/check` - Check specific permission
- `GET /api/v1/rbac/roles/templates` - List role templates

#### Bulk Operations
- `POST /api/v1/rbac/bulk/grant-access` - Bulk access grant

#### System Management
- `GET /api/v1/rbac/system/status` - RBAC system status

## 🚀 Quick Start

### 1. Database Setup

Create the central RBAC database:

```sql
CREATE DATABASE rbac_central CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'rbac_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON rbac_central.* TO 'rbac_user'@'localhost';
```

Apply the schema:

```bash
mysql -u rbac_user -p rbac_central < rbac_schemas/rbac_central_database.sql
```

### 2. Configuration

Update the RBAC configuration in `src/main.py`:

```python
RBAC_DB_CONFIG = {
    "type": "mysql",
    "connection": {
        "host": "localhost",
        "port": 3306,
        "database": "rbac_central",
        "user": "rbac_user",
        "password": "secure_password",
        "charset": "utf8mb4"
    }
}

JWT_SECRET = "your-super-secret-jwt-key-change-in-production"
```

### 3. Initialize System

The system automatically initializes role templates on startup:

```bash
python -m src.main
```

### 4. Create First User

```bash
curl -X POST "http://localhost:8000/api/v1/rbac/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "username": "admin",
    "email": "admin@company.com",
    "password": "secure_password",
    "full_name": "System Administrator",
    "is_global_admin": true
  }'
```

## 🔐 Authentication Flow

### 1. User Login

```python
# Login with tenant context
response = requests.post("/api/v1/rbac/auth/login", json={
    "username_or_email": "user@company.com",
    "password": "password",
    "tenant_id": "tenant_001"
})

token = response.json()["access_token"]
```

### 2. API Requests

```python
# Make authenticated requests
headers = {
    "Authorization": f"Bearer {token}",
    "X-Tenant-ID": "tenant_001"
}

response = requests.get("/api/v1/queries", headers=headers)
```

### 3. Permission Checking

```python
# Check specific permission
response = requests.post("/api/v1/rbac/permissions/check",
    headers=headers,
    json={
        "resource": "QUERIES",
        "level": "CREATE",
        "conditions": {"scope": "tenant_only"}
    }
)
```

## 🛡️ Security Features

### 1. Password Security
- PBKDF2 hashing with 100,000 iterations
- Random salt generation
- Secure password comparison

### 2. JWT Security
- HS256 algorithm (configurable)
- Configurable expiration times
- Token validation with session tracking
- Automatic token refresh

### 3. Permission System
```python
# Granular permissions with conditions
permission = Permission(
    resource=ResourceType.QUERIES,
    level=PermissionLevel.CREATE,
    conditions={"own_queries_only": True}
)
```

### 4. Audit Logging
- Complete operation tracking
- IP address and user agent logging
- Automatic retention management
- Security event detection

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_rbac_system.py
```

Test categories:
- System initialization
- Role template management
- User management
- Authentication
- Authorization
- Cross-tenant access
- Session management
- Security scenarios
- Performance testing
- Cleanup operations

## 📊 Performance Metrics

Expected performance benchmarks:
- **Authentication**: < 100ms per request
- **Permission Check**: < 10ms per request
- **JWT Validation**: < 5ms per request
- **Session Creation**: < 50ms per request

## 🔧 Configuration Options

### JWT Configuration
```python
JWT_CONFIG = {
    "secret": "your-secret-key",
    "algorithm": "HS256",
    "access_token_expire_minutes": 60,
    "refresh_token_expire_days": 30
}
```

### Session Configuration
```python
SESSION_CONFIG = {
    "timeout_hours": 8,
    "max_concurrent_sessions": 3,
    "cleanup_interval_hours": 1
}
```

### Permission Configuration
```python
PERMISSION_CONFIG = {
    "cache_permissions": True,
    "cache_timeout_minutes": 15,
    "enable_inheritance": True
}
```

## 🚦 Integration with Existing System

The RBAC system integrates seamlessly with the existing Multi-Tenant NLP2SQL system:

### 1. Protected Routes
```python
@app.get("/api/v1/queries")
async def list_queries(
    tenant_context: TenantContext = Depends(
        rbac_deps.require_permission(ResourceType.QUERIES, PermissionLevel.READ)
    )
):
    # Access tenant_context.user_id, tenant_context.tenant_id
    # Route automatically protected by RBAC
```

### 2. Tenant Context Access
```python
def get_tenant_database(tenant_context: TenantContext):
    # Get tenant-specific database connection
    return database_cloner.get_tenant_connection(tenant_context.tenant_id)
```

### 3. User Information
```python
def log_query_execution(query, tenant_context: TenantContext):
    # Log with user and tenant context
    logger.info(f"Query executed by {tenant_context.user_id} in {tenant_context.tenant_id}")
```

## 🔄 Migration from Existing Auth

To migrate from the existing authentication system:

1. **Export existing users**:
```python
# Export current users to RBAC system
for user in existing_users:
    rbac_manager.create_user(
        username=user.username,
        email=user.email,
        password=user.hashed_password,  # Will be re-hashed
        full_name=user.full_name
    )
```

2. **Grant tenant access**:
```python
# Grant access based on existing permissions
for user in users:
    rbac_manager.grant_tenant_access(
        user.id,
        user.organization_id,
        [map_role(user.role)],
        "system_migration"
    )
```

3. **Update frontend**:
```javascript
// Update login to use new RBAC endpoints
const response = await fetch('/api/v1/rbac/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        username_or_email: username,
        password: password,
        tenant_id: selectedTenant
    })
});
```

## 📈 Monitoring and Maintenance

### 1. Health Checks
```bash
curl http://localhost:8000/api/v1/rbac/system/status
```

### 2. Cleanup Operations
```python
# Automatic cleanup (run via cron)
rbac_manager.cleanup_expired_sessions()
cross_tenant_manager.cleanup_expired_access_requests()
```

### 3. Performance Monitoring
```python
# Monitor key metrics
- Authentication response time
- Permission check frequency
- Session creation rate
- Token validation errors
```

## 🤝 API Examples

### Complete User Journey

```python
import requests

base_url = "http://localhost:8000"

# 1. Admin creates user
admin_headers = {"Authorization": "Bearer admin_token"}
user_response = requests.post(f"{base_url}/api/v1/rbac/users",
    headers=admin_headers,
    json={
        "username": "analyst1",
        "email": "analyst1@company.com",
        "password": "secure_pass",
        "full_name": "Data Analyst"
    }
)
user_id = user_response.json()["user_id"]

# 2. Grant tenant access
requests.post(f"{base_url}/api/v1/rbac/access/grant",
    headers=admin_headers,
    json={
        "user_id": user_id,
        "tenant_id": "tenant_001",
        "role_names": ["analyst"]
    }
)

# 3. User login
login_response = requests.post(f"{base_url}/api/v1/rbac/auth/login",
    json={
        "username_or_email": "analyst1",
        "password": "secure_pass",
        "tenant_id": "tenant_001"
    }
)
token = login_response.json()["access_token"]

# 4. Make authenticated request
user_headers = {
    "Authorization": f"Bearer {token}",
    "X-Tenant-ID": "tenant_001"
}
queries = requests.get(f"{base_url}/api/v1/queries", headers=user_headers)

# 5. Check specific permission
perm_check = requests.post(f"{base_url}/api/v1/rbac/permissions/check",
    headers=user_headers,
    json={
        "resource": "QUERIES",
        "level": "CREATE"
    }
)
can_create = perm_check.json()["has_permission"]
```

## 🎯 Summary

The Enhanced RBAC Layer Integration provides:

✅ **Complete Security**: Enterprise-grade authentication and authorization
✅ **Tenant Isolation**: Perfect separation between tenant data and access
✅ **Scalable Architecture**: Supports hundreds of tenants and thousands of users
✅ **Flexible Permissions**: Granular control over resource access
✅ **Cross-Tenant Support**: Users can access multiple tenants with different roles
✅ **Audit Compliance**: Complete audit trail for regulatory requirements
✅ **High Performance**: Optimized for sub-10ms permission checks
✅ **Production Ready**: Comprehensive testing and monitoring

The system is now ready for enterprise deployment with complete multi-tenant isolation, role-based access control, and comprehensive user management capabilities.