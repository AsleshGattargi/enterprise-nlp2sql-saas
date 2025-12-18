"""
Cross-Tenant User Management System
Handles user management across multiple tenants with comprehensive access control.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import mysql.connector
import psycopg2
import sqlite3

from .tenant_rbac_manager import TenantRBACManager, UserProfile, UserStatus
from .rbac_role_templates import RoleTemplateManager, ResourceType, PermissionLevel


class AccessRequestStatus(Enum):
    """Status of tenant access requests."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class BulkOperationType(Enum):
    """Types of bulk operations."""
    GRANT_ACCESS = "GRANT_ACCESS"
    REVOKE_ACCESS = "REVOKE_ACCESS"
    UPDATE_ROLES = "UPDATE_ROLES"
    MIGRATE_USERS = "MIGRATE_USERS"


@dataclass
class TenantAccessRequest:
    """Request for tenant access."""
    request_id: str
    user_id: str
    tenant_id: str
    requested_roles: List[str]
    justification: str
    status: AccessRequestStatus
    requested_by: str
    requested_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BulkOperation:
    """Bulk operation tracking."""
    operation_id: str
    operation_type: BulkOperationType
    user_ids: List[str]
    tenant_ids: List[str]
    parameters: Dict[str, Any]
    initiated_by: str
    status: str
    progress: int
    total_items: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    errors: Optional[List[str]] = None


@dataclass
class CrossTenantUserSummary:
    """Summary of user access across tenants."""
    user_id: str
    username: str
    email: str
    full_name: str
    total_tenants: int
    active_tenants: int
    global_admin: bool
    tenant_roles: Dict[str, List[str]]  # tenant_id -> roles
    last_activity: Dict[str, datetime]  # tenant_id -> last_activity
    created_at: datetime


class CrossTenantUserManager:
    """Manages users across multiple tenants with advanced access control."""

    def __init__(self, rbac_manager: TenantRBACManager):
        self.rbac_manager = rbac_manager
        self.role_manager = rbac_manager.role_manager

    def get_connection(self):
        """Get database connection."""
        return self.rbac_manager.get_connection()

    def request_tenant_access(self, user_id: str, tenant_id: str, requested_roles: List[str],
                            justification: str, requested_by: str,
                            expires_in_days: int = 30) -> str:
        """Request access to a tenant with specified roles."""
        request_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if user exists
            cursor.execute("SELECT user_id FROM master_users WHERE user_id = %s", (user_id,))
            if not cursor.fetchone():
                raise ValueError(f"User not found: {user_id}")

            # Validate requested roles
            invalid_roles = []
            for role_name in requested_roles:
                role_template = self.role_manager.get_role_template(role_name)
                if not role_template or not role_template.is_assignable:
                    invalid_roles.append(role_name)

            if invalid_roles:
                raise ValueError(f"Invalid or non-assignable roles: {invalid_roles}")

            # Check for existing pending request
            cursor.execute("""
                SELECT request_id FROM tenant_access_requests
                WHERE user_id = %s AND tenant_id = %s AND status = %s
            """, (user_id, tenant_id, AccessRequestStatus.PENDING.value))

            if cursor.fetchone():
                raise ValueError("Pending access request already exists for this user and tenant")

            try:
                # Create access request record (we need to add this table to schema)
                cursor.execute("""
                    INSERT INTO tenant_access_requests
                    (request_id, user_id, tenant_id, requested_roles, justification,
                     status, requested_by, requested_at, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    request_id, user_id, tenant_id, json.dumps(requested_roles),
                    justification, AccessRequestStatus.PENDING.value,
                    requested_by, datetime.utcnow(), expires_at
                ))

                conn.commit()
                self.rbac_manager._log_rbac_action("ACCESS_REQUEST_CREATED", user_id, {
                    "request_id": request_id,
                    "tenant_id": tenant_id,
                    "requested_roles": requested_roles,
                    "requested_by": requested_by
                })

                return request_id

            except Exception as e:
                raise RuntimeError(f"Failed to create access request: {e}")

    def approve_access_request(self, request_id: str, reviewed_by: str) -> bool:
        """Approve a tenant access request."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get request details
            cursor.execute("""
                SELECT user_id, tenant_id, requested_roles, status, expires_at
                FROM tenant_access_requests
                WHERE request_id = %s
            """, (request_id,))

            request_data = cursor.fetchone()
            if not request_data:
                return False

            user_id, tenant_id, requested_roles_json, status, expires_at = request_data
            requested_roles = json.loads(requested_roles_json)

            if status != AccessRequestStatus.PENDING.value:
                return False

            if expires_at < datetime.utcnow():
                # Mark as expired
                cursor.execute("""
                    UPDATE tenant_access_requests
                    SET status = %s, reviewed_by = %s, reviewed_at = %s
                    WHERE request_id = %s
                """, (AccessRequestStatus.EXPIRED.value, reviewed_by, datetime.utcnow(), request_id))
                conn.commit()
                return False

            try:
                # Grant tenant access
                success = self.rbac_manager.grant_tenant_access(
                    user_id, tenant_id, requested_roles, reviewed_by
                )

                if success:
                    # Update request status
                    cursor.execute("""
                        UPDATE tenant_access_requests
                        SET status = %s, reviewed_by = %s, reviewed_at = %s
                        WHERE request_id = %s
                    """, (AccessRequestStatus.APPROVED.value, reviewed_by, datetime.utcnow(), request_id))

                    conn.commit()
                    self.rbac_manager._log_rbac_action("ACCESS_REQUEST_APPROVED", user_id, {
                        "request_id": request_id,
                        "tenant_id": tenant_id,
                        "roles_granted": requested_roles,
                        "reviewed_by": reviewed_by
                    })

                return success

            except Exception as e:
                print(f"Failed to approve access request: {e}")
                return False

    def reject_access_request(self, request_id: str, reviewed_by: str, reason: str = "") -> bool:
        """Reject a tenant access request."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    UPDATE tenant_access_requests
                    SET status = %s, reviewed_by = %s, reviewed_at = %s, rejection_reason = %s
                    WHERE request_id = %s AND status = %s
                """, (AccessRequestStatus.REJECTED.value, reviewed_by, datetime.utcnow(),
                      reason, request_id, AccessRequestStatus.PENDING.value))

                if cursor.rowcount > 0:
                    conn.commit()
                    self.rbac_manager._log_rbac_action("ACCESS_REQUEST_REJECTED", "system", {
                        "request_id": request_id,
                        "reviewed_by": reviewed_by,
                        "reason": reason
                    })
                    return True

                return False

            except Exception as e:
                print(f"Failed to reject access request: {e}")
                return False

    def get_cross_tenant_user_summary(self, user_id: str) -> Optional[CrossTenantUserSummary]:
        """Get comprehensive summary of user's access across all tenants."""
        user_profile = self.rbac_manager.get_user_profile(user_id)
        if not user_profile:
            return None

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get last activity per tenant
            cursor.execute("""
                SELECT tenant_id, MAX(last_activity) as last_activity
                FROM tenant_access_sessions
                WHERE user_id = %s
                GROUP BY tenant_id
            """, (user_id,))

            last_activity = {}
            for tenant_id, activity in cursor.fetchall():
                last_activity[tenant_id] = activity

            return CrossTenantUserSummary(
                user_id=user_profile.user_id,
                username=user_profile.username,
                email=user_profile.email,
                full_name=user_profile.full_name,
                total_tenants=len(user_profile.tenant_access),
                active_tenants=len([t for t in user_profile.tenant_access.keys() if t in last_activity]),
                global_admin=user_profile.is_global_admin,
                tenant_roles=user_profile.tenant_access,
                last_activity=last_activity,
                created_at=user_profile.created_at
            )

    def list_users_across_tenants(self, tenant_ids: List[str]) -> Dict[str, List[CrossTenantUserSummary]]:
        """List users across multiple tenants."""
        users_by_tenant = {}

        for tenant_id in tenant_ids:
            tenant_users = self.rbac_manager.list_tenant_users(tenant_id)
            users_by_tenant[tenant_id] = []

            for user_profile in tenant_users:
                summary = self.get_cross_tenant_user_summary(user_profile.user_id)
                if summary:
                    users_by_tenant[tenant_id].append(summary)

        return users_by_tenant

    def find_users_with_multiple_tenant_access(self, min_tenants: int = 2) -> List[CrossTenantUserSummary]:
        """Find users with access to multiple tenants."""
        users_with_multiple_access = []

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT u.user_id, COUNT(DISTINCT utm.tenant_id) as tenant_count
                FROM master_users u
                JOIN user_tenant_mappings utm ON u.user_id = utm.user_id
                WHERE utm.is_active = 1
                GROUP BY u.user_id
                HAVING tenant_count >= %s
                ORDER BY tenant_count DESC
            """, (min_tenants,))

            for user_id, tenant_count in cursor.fetchall():
                summary = self.get_cross_tenant_user_summary(user_id)
                if summary:
                    users_with_multiple_access.append(summary)

        return users_with_multiple_access

    def initiate_bulk_operation(self, operation_type: BulkOperationType, user_ids: List[str],
                              tenant_ids: List[str], parameters: Dict[str, Any],
                              initiated_by: str) -> str:
        """Initiate a bulk operation on users."""
        operation_id = str(uuid.uuid4())

        with self.get_connection() as conn:
            cursor = conn.cursor()

            total_items = len(user_ids) * len(tenant_ids)

            try:
                cursor.execute("""
                    INSERT INTO bulk_operations
                    (operation_id, operation_type, user_ids, tenant_ids, parameters,
                     initiated_by, status, progress, total_items, started_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    operation_id, operation_type.value, json.dumps(user_ids),
                    json.dumps(tenant_ids), json.dumps(parameters),
                    initiated_by, "INITIATED", 0, total_items, datetime.utcnow()
                ))

                conn.commit()
                self.rbac_manager._log_rbac_action("BULK_OPERATION_INITIATED", initiated_by, {
                    "operation_id": operation_id,
                    "operation_type": operation_type.value,
                    "user_count": len(user_ids),
                    "tenant_count": len(tenant_ids)
                })

                return operation_id

            except Exception as e:
                raise RuntimeError(f"Failed to initiate bulk operation: {e}")

    def execute_bulk_grant_access(self, operation_id: str) -> bool:
        """Execute bulk grant access operation."""
        operation = self._get_bulk_operation(operation_id)
        if not operation or operation.operation_type != BulkOperationType.GRANT_ACCESS:
            return False

        roles = operation.parameters.get("roles", [])
        if not roles:
            return False

        progress = 0
        errors = []

        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Update status to running
                cursor.execute("""
                    UPDATE bulk_operations SET status = %s WHERE operation_id = %s
                """, ("RUNNING", operation_id))
                conn.commit()

                for user_id in operation.user_ids:
                    for tenant_id in operation.tenant_ids:
                        try:
                            success = self.rbac_manager.grant_tenant_access(
                                user_id, tenant_id, roles, operation.initiated_by
                            )

                            if not success:
                                errors.append(f"Failed to grant access for user {user_id} to tenant {tenant_id}")

                            progress += 1

                            # Update progress
                            cursor.execute("""
                                UPDATE bulk_operations SET progress = %s WHERE operation_id = %s
                            """, (progress, operation_id))
                            conn.commit()

                        except Exception as e:
                            errors.append(f"Error granting access for user {user_id} to tenant {tenant_id}: {e}")
                            progress += 1

                # Update final status
                status = "COMPLETED" if not errors else "COMPLETED_WITH_ERRORS"
                cursor.execute("""
                    UPDATE bulk_operations
                    SET status = %s, completed_at = %s, errors = %s
                    WHERE operation_id = %s
                """, (status, datetime.utcnow(), json.dumps(errors) if errors else None, operation_id))

                conn.commit()
                return True

            except Exception as e:
                # Mark as failed
                cursor.execute("""
                    UPDATE bulk_operations
                    SET status = %s, completed_at = %s, errors = %s
                    WHERE operation_id = %s
                """, ("FAILED", datetime.utcnow(), json.dumps([str(e)]), operation_id))
                conn.commit()
                return False

    def _get_bulk_operation(self, operation_id: str) -> Optional[BulkOperation]:
        """Get bulk operation details."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT operation_id, operation_type, user_ids, tenant_ids, parameters,
                       initiated_by, status, progress, total_items, started_at,
                       completed_at, errors
                FROM bulk_operations
                WHERE operation_id = %s
            """, (operation_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return BulkOperation(
                operation_id=row[0],
                operation_type=BulkOperationType(row[1]),
                user_ids=json.loads(row[2]),
                tenant_ids=json.loads(row[3]),
                parameters=json.loads(row[4]),
                initiated_by=row[5],
                status=row[6],
                progress=row[7],
                total_items=row[8],
                started_at=row[9],
                completed_at=row[10],
                errors=json.loads(row[11]) if row[11] else None
            )

    def generate_user_access_report(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive access report for a user."""
        summary = self.get_cross_tenant_user_summary(user_id)
        if not summary:
            return {}

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get recent sessions
            cursor.execute("""
                SELECT tenant_id, session_id, created_at, last_activity, status
                FROM tenant_access_sessions
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 20
            """, (user_id,))

            recent_sessions = [
                {
                    "tenant_id": row[0],
                    "session_id": row[1],
                    "created_at": row[2].isoformat(),
                    "last_activity": row[3].isoformat(),
                    "status": row[4]
                }
                for row in cursor.fetchall()
            ]

            # Get access requests
            cursor.execute("""
                SELECT request_id, tenant_id, requested_roles, status, requested_at,
                       reviewed_by, reviewed_at
                FROM tenant_access_requests
                WHERE user_id = %s
                ORDER BY requested_at DESC
                LIMIT 10
            """, (user_id,))

            access_requests = [
                {
                    "request_id": row[0],
                    "tenant_id": row[1],
                    "requested_roles": json.loads(row[2]),
                    "status": row[3],
                    "requested_at": row[4].isoformat(),
                    "reviewed_by": row[5],
                    "reviewed_at": row[6].isoformat() if row[6] else None
                }
                for row in cursor.fetchall()
            ]

            return {
                "user_summary": {
                    "user_id": summary.user_id,
                    "username": summary.username,
                    "email": summary.email,
                    "full_name": summary.full_name,
                    "global_admin": summary.global_admin,
                    "total_tenants": summary.total_tenants,
                    "active_tenants": summary.active_tenants,
                    "created_at": summary.created_at.isoformat()
                },
                "tenant_access": {
                    tenant_id: {
                        "roles": roles,
                        "last_activity": summary.last_activity.get(tenant_id).isoformat() if summary.last_activity.get(tenant_id) else None
                    }
                    for tenant_id, roles in summary.tenant_roles.items()
                },
                "recent_sessions": recent_sessions,
                "access_requests": access_requests,
                "generated_at": datetime.utcnow().isoformat()
            }

    def cleanup_expired_access_requests(self) -> int:
        """Clean up expired access requests."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE tenant_access_requests
                SET status = %s
                WHERE status = %s AND expires_at < %s
            """, (AccessRequestStatus.EXPIRED.value, AccessRequestStatus.PENDING.value, datetime.utcnow()))

            expired_count = cursor.rowcount
            conn.commit()

            if expired_count > 0:
                self.rbac_manager._log_rbac_action("ACCESS_REQUESTS_EXPIRED", "system", {
                    "expired_count": expired_count
                })

            return expired_count