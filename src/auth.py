import bcrypt
import jwt
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
import os
from src.models import User, Organization, UserHDTAssignment, HumanDigitalTwin, HDTAgent, Agent
from src.database import db_manager
import logging

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

security = HTTPBearer()

class AuthManager:
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def extract_domain_from_email(self, email: str) -> str:
        """Extract domain from email for organization detection"""
        if "@" not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        domain_part = email.split("@")[1]
        return f"@{domain_part}"
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return user info with organization and HDT"""
        try:
            with db_manager.get_metadata_db() as db:
                # Extract domain for organization detection
                domain = self.extract_domain_from_email(email)
                
                # Find organization by domain
                organization = db.query(Organization).filter(
                    Organization.domain == domain
                ).first()
                
                if not organization:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Organization not found for this email domain"
                    )
                
                # Find user by email and organization
                user = db.query(User).filter(
                    User.email == email,
                    User.org_id == organization.org_id,
                    User.is_active == True
                ).first()
                
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found or inactive"
                    )
                
                # Verify password
                if not self.verify_password(password, user.password_hash):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Incorrect password"
                    )
                
                # Get user's HDT assignment
                hdt_assignment = db.query(UserHDTAssignment).filter(
                    UserHDTAssignment.user_id == user.user_id
                ).first()
                
                hdt = None
                hdt_agents = []
                if hdt_assignment:
                    hdt = db.query(HumanDigitalTwin).filter(
                        HumanDigitalTwin.hdt_id == hdt_assignment.hdt_id
                    ).first()
                    
                    # Get agents for this HDT
                    if hdt:
                        hdt_agent_assignments = db.query(HDTAgent).filter(
                            HDTAgent.hdt_id == hdt.hdt_id
                        ).all()
                        
                        for hdt_agent in hdt_agent_assignments:
                            agent = db.query(Agent).filter(
                                Agent.agent_id == hdt_agent.agent_id
                            ).first()
                            if agent:
                                hdt_agents.append(agent.agent_name)
                
                # Create access token
                token_data = {
                    "user_id": user.user_id,
                    "org_id": organization.org_id,
                    "email": user.email,
                    "role": user.role,
                    "hdt_id": hdt.hdt_id if hdt else None
                }
                
                access_token = self.create_access_token(token_data)
                
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": {
                        "user_id": user.user_id,
                        "org_id": user.org_id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                        "department": user.department,
                        "role": user.role,
                        "is_active": user.is_active
                    },
                    "organization": {
                        "org_id": organization.org_id,
                        "org_name": organization.org_name,
                        "domain": organization.domain,
                        "database_type": organization.database_type,
                        "database_name": organization.database_name,
                        "industry": organization.industry
                    },
                    "hdt": {
                        "hdt_id": hdt.hdt_id,
                        "name": hdt.name,
                        "description": hdt.description,
                        "context": hdt.context,
                        "skillset": json.loads(hdt.skillset) if hdt.skillset else [],
                        "languages": json.loads(hdt.languages) if hdt.languages else [],
                        "agents": hdt_agents
                    } if hdt else None
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Get current user from JWT token"""
        token = credentials.credentials
        payload = self.verify_token(token)
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return payload
    
    def check_user_permission(self, user_id: str, resource_type: str, resource_name: str, required_access: str) -> bool:
        """Check if user has permission for specific resource based on role"""
        try:
            with db_manager.get_metadata_db() as db:
                from src.models import UserPermission, User, Organization

                # First check explicit user permissions (if any)
                permission = db.query(UserPermission).filter(
                    UserPermission.user_id == user_id,
                    UserPermission.resource_type == resource_type,
                    UserPermission.resource_name == resource_name
                ).first()

                if permission:
                    # Check access level hierarchy: admin > write > read
                    access_hierarchy = {"read": 1, "write": 2, "admin": 3}
                    user_level = access_hierarchy.get(permission.access_level, 0)
                    required_level = access_hierarchy.get(required_access, 0)
                    return user_level >= required_level

                # If no explicit permission, use role-based access
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    return False

                # Role-based permissions - only READ access for non-admins
                if user.role == 'admin':
                    return True  # Admin has full access to everything

                # All other roles are READ-ONLY
                if required_access != 'read':
                    return False

                # Get user's organization to determine industry-specific access
                user_org = db.query(Organization).filter(Organization.org_id == user.org_id).first()
                industry = user_org.industry if user_org else None

                # Role-based table access by industry
                if user.role == 'manager':
                    # Managers can see operational data relevant to their department
                    if industry == 'Finance':
                        allowed_tables = ['accounts', 'transactions', 'customers', 'branches']
                    elif industry == 'Healthcare':
                        allowed_tables = ['patients', 'appointments', 'doctors', 'departments', 'billing']
                    elif industry == 'Technology':
                        allowed_tables = ['products', 'inventory', 'sales', 'customers', 'employees']
                    elif industry == 'Retail':
                        allowed_tables = ['products', 'customers', 'orders', 'inventory', 'sales_analytics']
                    elif industry == 'Education':
                        allowed_tables = ['students', 'courses', 'enrollments', 'instructors', 'departments']
                    else:
                        allowed_tables = ['products', 'customers']
                    return resource_name in allowed_tables

                elif user.role == 'analyst':
                    # Analysts can see analytical/reporting data
                    if industry == 'Finance':
                        allowed_tables = ['accounts', 'transactions', 'investments']  # No customer PII
                    elif industry == 'Healthcare':
                        allowed_tables = ['appointments', 'treatments', 'billing']  # No patient PII
                    elif industry == 'Technology':
                        allowed_tables = ['products', 'sales', 'inventory']  # No employee/customer PII
                    elif industry == 'Retail':
                        allowed_tables = ['products', 'orders', 'sales_analytics', 'reviews']  # No customer PII
                    elif industry == 'Education':
                        allowed_tables = ['courses', 'enrollments', 'grades', 'assignments']  # No student PII
                    else:
                        allowed_tables = ['products', 'sales']
                    return resource_name in allowed_tables

                elif user.role == 'developer':
                    # Developers can see technical/system data
                    if industry == 'Finance':
                        allowed_tables = ['accounts', 'transactions']  # Basic financial data
                    elif industry == 'Healthcare':
                        allowed_tables = ['appointments', 'treatments']  # Basic healthcare data
                    elif industry == 'Technology':
                        allowed_tables = ['products', 'inventory']  # Product/technical data
                    elif industry == 'Retail':
                        allowed_tables = ['products', 'inventory']  # Product/inventory data
                    elif industry == 'Education':
                        allowed_tables = ['courses', 'assignments']  # Course/assignment data
                    else:
                        allowed_tables = ['products']
                    return resource_name in allowed_tables

                elif user.role == 'viewer':
                    # Viewers can only see basic public data
                    if industry == 'Finance':
                        allowed_tables = ['accounts']  # Basic account info only
                    elif industry == 'Healthcare':
                        allowed_tables = ['appointments']  # Basic appointment info only
                    elif industry == 'Technology':
                        allowed_tables = ['products']  # Product catalog only
                    elif industry == 'Retail':
                        allowed_tables = ['products']  # Product catalog only
                    elif industry == 'Education':
                        allowed_tables = ['courses']  # Course catalog only
                    else:
                        allowed_tables = ['products']
                    return resource_name in allowed_tables

                return False

        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False
    
    def get_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """Get all permissions for a user"""
        try:
            with db_manager.get_metadata_db() as db:
                from src.models import UserPermission
                
                permissions = db.query(UserPermission).filter(
                    UserPermission.user_id == user_id
                ).all()
                
                permission_list = []
                for perm in permissions:
                    permission_list.append({
                        "resource_type": perm.resource_type,
                        "resource_name": perm.resource_name,
                        "access_level": perm.access_level
                    })
                
                return {
                    "user_id": user_id,
                    "permissions": permission_list
                }
                
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return {"user_id": user_id, "permissions": []}
    
    def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Get user information by user ID"""
        try:
            with db_manager.get_metadata_db() as db:
                from src.models import User
                
                user = db.query(User).filter(User.user_id == user_id).first()
                if user:
                    return {
                        'user_id': user.user_id,
                        'username': user.username,
                        'email': user.email,
                        'full_name': user.full_name,
                        'role': user.role,
                        'department': user.department,
                        'is_active': user.is_active
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def require_role(self, required_roles: list):
        """Decorator to require specific roles"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                current_user = kwargs.get('current_user')
                if not current_user or current_user.get('role') not in required_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient privileges"
                    )
                return func(*args, **kwargs)
            return wrapper
        return decorator

# Global auth manager instance
auth_manager = AuthManager()

# Dependency for getting current user
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    return auth_manager.get_current_user(credentials)

# Dependency for admin-only endpoints
def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

# Dependency for manager+ level access
def get_manager_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    allowed_roles = ["admin", "manager"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager privileges or higher required"
        )
    return current_user