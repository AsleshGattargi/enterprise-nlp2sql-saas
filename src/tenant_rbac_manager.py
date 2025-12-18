"""
TenantRBACManager - Core RBAC management for multi-tenant system
Handles user authentication, authorization, and tenant access control.
"""

import json
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Tuple, Union
import mysql.connector
import psycopg2
import sqlite3
import jwt
from dataclasses import dataclass
from enum import Enum

from .rbac_role_templates import RoleTemplateManager, ResourceType, PermissionLevel, Permission


class UserStatus(Enum):
    """User account status."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class SessionStatus(Enum):
    """Session status."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    INVALID = "INVALID"


@dataclass
class UserProfile:
    """User profile with tenant access information."""
    user_id: str
    username: str
    email: str
    full_name: str
    is_global_admin: bool
    status: UserStatus
    tenant_access: Dict[str, List[str]]  # tenant_id -> list of role names
    created_at: datetime
    last_login: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TenantSession:
    """Active tenant session information."""
    session_id: str
    user_id: str
    tenant_id: str
    roles: List[str]
    permissions: Set[Permission]
    expires_at: datetime
    created_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TenantRBACManager:
    """Comprehensive RBAC manager for multi-tenant system."""

    def __init__(self, rbac_db_config: Dict[str, Any], jwt_secret: str, jwt_algorithm: str = "HS256"):
        """Initialize RBAC manager with database and JWT configuration."""
        self.rbac_db_config = rbac_db_config
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.role_manager = RoleTemplateManager(rbac_db_config)
        self._session_timeout = timedelta(hours=8)  # Default session timeout

    def get_connection(self):
        """Get database connection to RBAC central database."""
        db_type = self.rbac_db_config.get("type", "mysql")

        if db_type == "mysql":
            return mysql.connector.connect(**self.rbac_db_config["connection"])
        elif db_type == "postgresql":
            return psycopg2.connect(**self.rbac_db_config["connection"])
        elif db_type == "sqlite":
            return sqlite3.connect(self.rbac_db_config["connection"]["database"])
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def _hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash password with salt."""
        if salt is None:
            salt = secrets.token_hex(32)

        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return password_hash.hex(), salt

    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash."""
        computed_hash, _ = self._hash_password(password, salt)
        return secrets.compare_digest(computed_hash, password_hash)

    def create_user(self, username: str, email: str, password: str, full_name: str,
                   is_global_admin: bool = False, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a new user in the central RBAC system."""
        user_id = str(uuid.uuid4())
        password_hash, salt = self._hash_password(password)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Check if username or email already exists
                cursor.execute("""
                    SELECT user_id FROM master_users
                    WHERE username = %s OR email = %s
                """, (username, email))

                if cursor.fetchone():
                    return None  # User already exists

                # Insert new user
                cursor.execute("""
                    INSERT INTO master_users
                    (user_id, username, email, password_hash, password_salt, full_name,
                     is_global_admin, status, metadata, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id, username, email, password_hash, salt, full_name,
                    is_global_admin, UserStatus.ACTIVE.value,
                    json.dumps(metadata) if metadata else None,
                    datetime.utcnow(), datetime.utcnow()
                ))

                conn.commit()
                self._log_rbac_action("USER_CREATED", user_id, {"username": username, "email": email})
                return user_id

            except Exception as e:
                print(f"Failed to create user: {e}")
                return None

    def authenticate_user(self, username_or_email: str, password: str) -> Optional[UserProfile]:
        """Authenticate user and return profile if successful."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT user_id, username, email, password_hash, password_salt, full_name,
                       is_global_admin, status, metadata, created_at, last_login
                FROM master_users
                WHERE (username = %s OR email = %s) AND status = %s
            """, (username_or_email, username_or_email, UserStatus.ACTIVE.value))

            user_data = cursor.fetchone()
            if not user_data:
                return None

            # Verify password
            if not self._verify_password(password, user_data[3], user_data[4]):
                return None

            # Update last login
            cursor.execute("""
                UPDATE master_users SET last_login = %s WHERE user_id = %s
            """, (datetime.utcnow(), user_data[0]))
            conn.commit()

            # Get tenant access information
            tenant_access = self._get_user_tenant_access(user_data[0])

            user_profile = UserProfile(
                user_id=user_data[0],
                username=user_data[1],
                email=user_data[2],
                full_name=user_data[5],
                is_global_admin=bool(user_data[6]),
                status=UserStatus(user_data[7]),
                tenant_access=tenant_access,
                created_at=user_data[9],
                last_login=user_data[10],
                metadata=json.loads(user_data[8]) if user_data[8] else None
            )

            self._log_rbac_action("USER_LOGIN", user_data[0], {"username": user_data[1]})
            return user_profile

    def _get_user_tenant_access(self, user_id: str) -> Dict[str, List[str]]:
        """Get user's tenant access mapping."""
        tenant_access = {}

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT utm.tenant_id, rt.role_name
                FROM user_tenant_mappings utm
                JOIN user_tenant_roles utr ON utm.user_id = utr.user_id AND utm.tenant_id = utr.tenant_id
                JOIN role_templates rt ON utr.role_template_id = rt.role_template_id
                WHERE utm.user_id = %s AND utm.is_active = 1 AND utr.is_active = 1
                ORDER BY utm.tenant_id, rt.role_name
            """, (user_id,))

            for tenant_id, role_name in cursor.fetchall():
                if tenant_id not in tenant_access:
                    tenant_access[tenant_id] = []
                tenant_access[tenant_id].append(role_name)

        return tenant_access

    def grant_tenant_access(self, user_id: str, tenant_id: str, role_names: List[str],
                           granted_by: str) -> bool:
        """Grant user access to tenant with specified roles."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Ensure user exists
                cursor.execute("SELECT user_id FROM master_users WHERE user_id = %s", (user_id,))
                if not cursor.fetchone():
                    return False

                # Check if tenant mapping exists
                cursor.execute("""
                    SELECT mapping_id FROM user_tenant_mappings
                    WHERE user_id = %s AND tenant_id = %s
                """, (user_id, tenant_id))

                mapping_data = cursor.fetchone()

                if not mapping_data:
                    # Create tenant mapping
                    mapping_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO user_tenant_mappings
                        (mapping_id, user_id, tenant_id, granted_by, granted_at, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (mapping_id, user_id, tenant_id, granted_by, datetime.utcnow(), True))
                else:
                    mapping_id = mapping_data[0]
                    # Activate mapping if inactive
                    cursor.execute("""
                        UPDATE user_tenant_mappings
                        SET is_active = 1, granted_by = %s, granted_at = %s
                        WHERE mapping_id = %s
                    """, (granted_by, datetime.utcnow(), mapping_id))

                # Add roles
                for role_name in role_names:
                    # Get role template ID
                    cursor.execute("""
                        SELECT role_template_id FROM role_templates
                        WHERE role_name = %s AND is_assignable = 1
                    """, (role_name,))

                    template_data = cursor.fetchone()
                    if not template_data:
                        continue

                    role_template_id = template_data[0]

                    # Check if role assignment already exists
                    cursor.execute("""
                        SELECT role_assignment_id FROM user_tenant_roles
                        WHERE user_id = %s AND tenant_id = %s AND role_template_id = %s
                    """, (user_id, tenant_id, role_template_id))

                    if cursor.fetchone():
                        # Update existing assignment
                        cursor.execute("""
                            UPDATE user_tenant_roles
                            SET is_active = 1, assigned_by = %s, assigned_at = %s
                            WHERE user_id = %s AND tenant_id = %s AND role_template_id = %s
                        """, (granted_by, datetime.utcnow(), user_id, tenant_id, role_template_id))
                    else:
                        # Create new role assignment
                        assignment_id = str(uuid.uuid4())
                        cursor.execute("""
                            INSERT INTO user_tenant_roles
                            (role_assignment_id, user_id, tenant_id, role_template_id,
                             assigned_by, assigned_at, is_active)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (assignment_id, user_id, tenant_id, role_template_id,
                             granted_by, datetime.utcnow(), True))

                conn.commit()
                self._log_rbac_action("TENANT_ACCESS_GRANTED", user_id, {
                    "tenant_id": tenant_id,
                    "roles": role_names,
                    "granted_by": granted_by
                })
                return True

            except Exception as e:
                print(f"Failed to grant tenant access: {e}")
                return False

    def revoke_tenant_access(self, user_id: str, tenant_id: str, revoked_by: str) -> bool:
        """Revoke user's access to tenant."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Deactivate tenant mapping
                cursor.execute("""
                    UPDATE user_tenant_mappings
                    SET is_active = 0, revoked_by = %s, revoked_at = %s
                    WHERE user_id = %s AND tenant_id = %s
                """, (revoked_by, datetime.utcnow(), user_id, tenant_id))

                # Deactivate all role assignments for this tenant
                cursor.execute("""
                    UPDATE user_tenant_roles
                    SET is_active = 0, revoked_by = %s, revoked_at = %s
                    WHERE user_id = %s AND tenant_id = %s
                """, (revoked_by, datetime.utcnow(), user_id, tenant_id))

                # Revoke active sessions for this tenant
                cursor.execute("""
                    UPDATE tenant_access_sessions
                    SET status = %s, ended_at = %s
                    WHERE user_id = %s AND tenant_id = %s AND status = %s
                """, (SessionStatus.REVOKED.value, datetime.utcnow(), user_id, tenant_id, SessionStatus.ACTIVE.value))

                conn.commit()
                self._log_rbac_action("TENANT_ACCESS_REVOKED", user_id, {
                    "tenant_id": tenant_id,
                    "revoked_by": revoked_by
                })
                return True

            except Exception as e:
                print(f"Failed to revoke tenant access: {e}")
                return False

    def create_tenant_session(self, user_id: str, tenant_id: str, ip_address: Optional[str] = None,
                            user_agent: Optional[str] = None) -> Optional[TenantSession]:
        """Create authenticated session for user in specific tenant."""
        # Verify user has access to tenant
        user_profile = self.get_user_profile(user_id)
        if not user_profile or tenant_id not in user_profile.tenant_access:
            return None

        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + self._session_timeout

        # Get user's roles and permissions for this tenant
        roles = user_profile.tenant_access[tenant_id]
        permissions = set()
        for role_name in roles:
            role_permissions = self.role_manager.resolve_role_permissions(role_name)
            permissions.update(role_permissions)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Create session record
                cursor.execute("""
                    INSERT INTO tenant_access_sessions
                    (session_id, user_id, tenant_id, roles, expires_at, status,
                     ip_address, user_agent, created_at, last_activity)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    session_id, user_id, tenant_id, json.dumps(roles), expires_at,
                    SessionStatus.ACTIVE.value, ip_address, user_agent,
                    datetime.utcnow(), datetime.utcnow()
                ))

                conn.commit()

                tenant_session = TenantSession(
                    session_id=session_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    roles=roles,
                    permissions=permissions,
                    expires_at=expires_at,
                    created_at=datetime.utcnow(),
                    last_activity=datetime.utcnow(),
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                self._log_rbac_action("SESSION_CREATED", user_id, {
                    "session_id": session_id,
                    "tenant_id": tenant_id,
                    "roles": roles
                })

                return tenant_session

            except Exception as e:
                print(f"Failed to create tenant session: {e}")
                return None

    def generate_jwt_token(self, tenant_session: TenantSession) -> str:
        """Generate JWT token for tenant session."""
        payload = {
            "session_id": tenant_session.session_id,
            "user_id": tenant_session.user_id,
            "tenant_id": tenant_session.tenant_id,
            "roles": tenant_session.roles,
            "exp": tenant_session.expires_at.timestamp(),
            "iat": datetime.utcnow().timestamp(),
            "iss": "multi-tenant-nlp2sql"
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            # Verify session is still active
            session_id = payload.get("session_id")
            if not self._is_session_active(session_id):
                return None

            # Update last activity
            self._update_session_activity(session_id)

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def _is_session_active(self, session_id: str) -> bool:
        """Check if session is still active."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT status, expires_at FROM tenant_access_sessions
                WHERE session_id = %s
            """, (session_id,))

            result = cursor.fetchone()
            if not result:
                return False

            status, expires_at = result
            return status == SessionStatus.ACTIVE.value and expires_at > datetime.utcnow()

    def _update_session_activity(self, session_id: str):
        """Update session last activity timestamp."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tenant_access_sessions
                SET last_activity = %s
                WHERE session_id = %s
            """, (datetime.utcnow(), session_id))
            conn.commit()

    def check_user_permission(self, user_id: str, tenant_id: str, resource: ResourceType,
                            level: PermissionLevel, conditions: Optional[Dict[str, Any]] = None) -> bool:
        """Check if user has specific permission in tenant."""
        return self.role_manager.check_permission(user_id, tenant_id, resource, level, conditions)

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT user_id, username, email, full_name, is_global_admin, status,
                       metadata, created_at, last_login
                FROM master_users
                WHERE user_id = %s
            """, (user_id,))

            user_data = cursor.fetchone()
            if not user_data:
                return None

            tenant_access = self._get_user_tenant_access(user_id)

            return UserProfile(
                user_id=user_data[0],
                username=user_data[1],
                email=user_data[2],
                full_name=user_data[3],
                is_global_admin=bool(user_data[4]),
                status=UserStatus(user_data[5]),
                tenant_access=tenant_access,
                created_at=user_data[7],
                last_login=user_data[8],
                metadata=json.loads(user_data[6]) if user_data[6] else None
            )

    def list_tenant_users(self, tenant_id: str) -> List[UserProfile]:
        """List all users with access to specific tenant."""
        users = []

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT u.user_id, u.username, u.email, u.full_name,
                       u.is_global_admin, u.status, u.metadata, u.created_at, u.last_login
                FROM master_users u
                JOIN user_tenant_mappings utm ON u.user_id = utm.user_id
                WHERE utm.tenant_id = %s AND utm.is_active = 1
                ORDER BY u.username
            """, (tenant_id,))

            for user_data in cursor.fetchall():
                tenant_access = self._get_user_tenant_access(user_data[0])

                users.append(UserProfile(
                    user_id=user_data[0],
                    username=user_data[1],
                    email=user_data[2],
                    full_name=user_data[3],
                    is_global_admin=bool(user_data[4]),
                    status=UserStatus(user_data[5]),
                    tenant_access=tenant_access,
                    created_at=user_data[7],
                    last_login=user_data[8],
                    metadata=json.loads(user_data[6]) if user_data[6] else None
                ))

        return users

    def _log_rbac_action(self, action: str, user_id: str, details: Dict[str, Any]):
        """Log RBAC action to audit trail."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                log_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO rbac_audit_log
                    (log_id, action, user_id, details, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                """, (log_id, action, user_id, json.dumps(details), datetime.utcnow()))
                conn.commit()
            except Exception as e:
                print(f"Failed to log RBAC action: {e}")

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and return count of cleaned sessions."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE tenant_access_sessions
                SET status = %s, ended_at = %s
                WHERE status = %s AND expires_at < %s
            """, (SessionStatus.EXPIRED.value, datetime.utcnow(),
                  SessionStatus.ACTIVE.value, datetime.utcnow()))

            cleaned_count = cursor.rowcount
            conn.commit()

            if cleaned_count > 0:
                self._log_rbac_action("SESSIONS_CLEANUP", "system", {"cleaned_count": cleaned_count})

            return cleaned_count