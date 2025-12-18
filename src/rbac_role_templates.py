"""
Role Template System for Multi-Tenant RBAC
Manages role definitions, permissions, and hierarchical inheritance.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Set, Optional, Any, Union
from enum import Enum
import mysql.connector
import psycopg2
import sqlite3
from dataclasses import dataclass


class PermissionLevel(Enum):
    """Permission levels for role-based access control."""
    NONE = "NONE"
    READ_ONLY = "READ_ONLY"
    READ = "READ"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    FULL_ACCESS = "FULL_ACCESS"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class ResourceType(Enum):
    """Resource types in the multi-tenant system."""
    QUERIES = "QUERIES"
    DATABASES = "DATABASES"
    SCHEMAS = "SCHEMAS"
    REPORTS = "REPORTS"
    USERS = "USERS"
    TENANTS = "TENANTS"
    SYSTEM = "SYSTEM"
    ANALYTICS = "ANALYTICS"
    API_TOKENS = "API_TOKENS"
    AUDIT_LOGS = "AUDIT_LOGS"


@dataclass
class Permission:
    """Individual permission definition."""
    resource: ResourceType
    level: PermissionLevel
    conditions: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RoleTemplate:
    """Role template with permissions and metadata."""
    role_name: str
    display_name: str
    description: str
    permissions: List[Permission]
    inherits_from: Optional[List[str]] = None
    is_system_role: bool = True
    is_assignable: bool = True
    metadata: Optional[Dict[str, Any]] = None


class RoleTemplateManager:
    """Manages role templates and permission systems."""

    def __init__(self, rbac_db_config: Dict[str, Any]):
        """Initialize with RBAC database configuration."""
        self.rbac_db_config = rbac_db_config
        self._initialize_default_templates()

    def _initialize_default_templates(self):
        """Initialize default role templates."""
        self.default_templates = {
            # Super Admin - Global system access
            "super_admin": RoleTemplate(
                role_name="super_admin",
                display_name="Super Administrator",
                description="Global system administrator with full access to all tenants and system functions",
                permissions=[
                    Permission(ResourceType.SYSTEM, PermissionLevel.SUPER_ADMIN),
                    Permission(ResourceType.TENANTS, PermissionLevel.SUPER_ADMIN),
                    Permission(ResourceType.USERS, PermissionLevel.SUPER_ADMIN),
                    Permission(ResourceType.DATABASES, PermissionLevel.SUPER_ADMIN),
                    Permission(ResourceType.QUERIES, PermissionLevel.SUPER_ADMIN),
                    Permission(ResourceType.REPORTS, PermissionLevel.SUPER_ADMIN),
                    Permission(ResourceType.ANALYTICS, PermissionLevel.SUPER_ADMIN),
                    Permission(ResourceType.API_TOKENS, PermissionLevel.SUPER_ADMIN),
                    Permission(ResourceType.AUDIT_LOGS, PermissionLevel.SUPER_ADMIN),
                ],
                is_system_role=True,
                is_assignable=False  # Only assignable by system
            ),

            # Tenant Admin - Full access within tenant
            "admin": RoleTemplate(
                role_name="admin",
                display_name="Tenant Administrator",
                description="Full administrative access within assigned tenant(s)",
                permissions=[
                    Permission(ResourceType.DATABASES, PermissionLevel.ADMIN),
                    Permission(ResourceType.SCHEMAS, PermissionLevel.ADMIN),
                    Permission(ResourceType.QUERIES, PermissionLevel.FULL_ACCESS),
                    Permission(ResourceType.REPORTS, PermissionLevel.FULL_ACCESS),
                    Permission(ResourceType.USERS, PermissionLevel.ADMIN,
                             conditions={"scope": "tenant_only"}),
                    Permission(ResourceType.ANALYTICS, PermissionLevel.FULL_ACCESS),
                    Permission(ResourceType.API_TOKENS, PermissionLevel.ADMIN,
                             conditions={"scope": "tenant_only"}),
                    Permission(ResourceType.AUDIT_LOGS, PermissionLevel.READ,
                             conditions={"scope": "tenant_only"}),
                ],
                is_system_role=True,
                is_assignable=True
            ),

            # Data Analyst - Query and analysis focus
            "analyst": RoleTemplate(
                role_name="analyst",
                display_name="Data Analyst",
                description="Can create, execute, and analyze queries with reporting capabilities",
                permissions=[
                    Permission(ResourceType.DATABASES, PermissionLevel.READ),
                    Permission(ResourceType.SCHEMAS, PermissionLevel.READ),
                    Permission(ResourceType.QUERIES, PermissionLevel.FULL_ACCESS,
                             conditions={"own_queries_only": False}),
                    Permission(ResourceType.REPORTS, PermissionLevel.CREATE),
                    Permission(ResourceType.ANALYTICS, PermissionLevel.READ),
                    Permission(ResourceType.API_TOKENS, PermissionLevel.READ,
                             conditions={"own_tokens_only": True}),
                ],
                is_system_role=True,
                is_assignable=True
            ),

            # Business User - Query creation and basic analysis
            "business_user": RoleTemplate(
                role_name="business_user",
                display_name="Business User",
                description="Can create basic queries and view reports",
                permissions=[
                    Permission(ResourceType.DATABASES, PermissionLevel.READ),
                    Permission(ResourceType.SCHEMAS, PermissionLevel.READ),
                    Permission(ResourceType.QUERIES, PermissionLevel.CREATE,
                             conditions={"templates_only": True}),
                    Permission(ResourceType.REPORTS, PermissionLevel.READ),
                    Permission(ResourceType.ANALYTICS, PermissionLevel.READ,
                             conditions={"basic_analytics_only": True}),
                ],
                is_system_role=True,
                is_assignable=True
            ),

            # Read-Only Viewer
            "viewer": RoleTemplate(
                role_name="viewer",
                display_name="Report Viewer",
                description="Read-only access to reports and basic query results",
                permissions=[
                    Permission(ResourceType.QUERIES, PermissionLevel.READ_ONLY,
                             conditions={"shared_queries_only": True}),
                    Permission(ResourceType.REPORTS, PermissionLevel.READ_ONLY),
                    Permission(ResourceType.ANALYTICS, PermissionLevel.READ_ONLY,
                             conditions={"basic_analytics_only": True}),
                ],
                is_system_role=True,
                is_assignable=True
            ),

            # API User - Programmatic access
            "api_user": RoleTemplate(
                role_name="api_user",
                display_name="API User",
                description="Programmatic access for API integrations",
                permissions=[
                    Permission(ResourceType.QUERIES, PermissionLevel.CREATE,
                             conditions={"api_mode": True}),
                    Permission(ResourceType.DATABASES, PermissionLevel.READ,
                             conditions={"api_mode": True}),
                    Permission(ResourceType.API_TOKENS, PermissionLevel.READ,
                             conditions={"own_tokens_only": True}),
                ],
                is_system_role=True,
                is_assignable=True,
                metadata={"rate_limits": {"queries_per_hour": 1000}}
            ),

            # Guest User - Minimal access
            "guest": RoleTemplate(
                role_name="guest",
                display_name="Guest User",
                description="Temporary limited access for demonstrations",
                permissions=[
                    Permission(ResourceType.QUERIES, PermissionLevel.READ_ONLY,
                             conditions={"demo_queries_only": True}),
                    Permission(ResourceType.REPORTS, PermissionLevel.READ_ONLY,
                             conditions={"public_reports_only": True}),
                ],
                is_system_role=True,
                is_assignable=False,  # Must be explicitly granted
                metadata={"session_timeout": 3600}  # 1 hour
            )
        }

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

    def install_default_templates(self) -> Dict[str, bool]:
        """Install default role templates into the database."""
        results = {}

        with self.get_connection() as conn:
            cursor = conn.cursor()

            for template_name, template in self.default_templates.items():
                try:
                    # Check if template already exists
                    cursor.execute(
                        "SELECT role_template_id FROM role_templates WHERE role_name = %s",
                        (template.role_name,)
                    )

                    existing = cursor.fetchone()

                    if existing:
                        # Update existing template
                        cursor.execute("""
                            UPDATE role_templates
                            SET display_name = %s, description = %s, permissions = %s,
                                inherits_from = %s, is_system_role = %s, is_assignable = %s,
                                metadata = %s, updated_at = %s
                            WHERE role_name = %s
                        """, (
                            template.display_name,
                            template.description,
                            json.dumps(self._serialize_permissions(template.permissions)),
                            json.dumps(template.inherits_from) if template.inherits_from else None,
                            template.is_system_role,
                            template.is_assignable,
                            json.dumps(template.metadata) if template.metadata else None,
                            datetime.utcnow(),
                            template.role_name
                        ))
                        results[template_name] = True
                    else:
                        # Insert new template
                        template_id = str(uuid.uuid4())
                        cursor.execute("""
                            INSERT INTO role_templates
                            (role_template_id, role_name, display_name, description, permissions,
                             inherits_from, is_system_role, is_assignable, metadata, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            template_id,
                            template.role_name,
                            template.display_name,
                            template.description,
                            json.dumps(self._serialize_permissions(template.permissions)),
                            json.dumps(template.inherits_from) if template.inherits_from else None,
                            template.is_system_role,
                            template.is_assignable,
                            json.dumps(template.metadata) if template.metadata else None,
                            datetime.utcnow(),
                            datetime.utcnow()
                        ))
                        results[template_name] = True

                except Exception as e:
                    print(f"Failed to install template {template_name}: {e}")
                    results[template_name] = False

            conn.commit()

        return results

    def _serialize_permissions(self, permissions: List[Permission]) -> List[Dict[str, Any]]:
        """Serialize permissions for database storage."""
        return [
            {
                "resource": perm.resource.value,
                "level": perm.level.value,
                "conditions": perm.conditions,
                "metadata": perm.metadata
            }
            for perm in permissions
        ]

    def _deserialize_permissions(self, permissions_data: List[Dict[str, Any]]) -> List[Permission]:
        """Deserialize permissions from database."""
        return [
            Permission(
                resource=ResourceType(perm["resource"]),
                level=PermissionLevel(perm["level"]),
                conditions=perm.get("conditions"),
                metadata=perm.get("metadata")
            )
            for perm in permissions_data
        ]

    def get_role_template(self, role_name: str) -> Optional[RoleTemplate]:
        """Get role template by name."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role_name, display_name, description, permissions, inherits_from,
                       is_system_role, is_assignable, metadata
                FROM role_templates
                WHERE role_name = %s AND is_active = 1
            """, (role_name,))

            row = cursor.fetchone()
            if not row:
                return None

            return RoleTemplate(
                role_name=row[0],
                display_name=row[1],
                description=row[2],
                permissions=self._deserialize_permissions(json.loads(row[3])),
                inherits_from=json.loads(row[4]) if row[4] else None,
                is_system_role=bool(row[5]),
                is_assignable=bool(row[6]),
                metadata=json.loads(row[7]) if row[7] else None
            )

    def list_role_templates(self, include_non_assignable: bool = False) -> List[RoleTemplate]:
        """List all available role templates."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT role_name, display_name, description, permissions, inherits_from,
                       is_system_role, is_assignable, metadata
                FROM role_templates
                WHERE is_active = 1
            """

            if not include_non_assignable:
                query += " AND is_assignable = 1"

            query += " ORDER BY role_name"

            cursor.execute(query)
            rows = cursor.fetchall()

            templates = []
            for row in rows:
                templates.append(RoleTemplate(
                    role_name=row[0],
                    display_name=row[1],
                    description=row[2],
                    permissions=self._deserialize_permissions(json.loads(row[3])),
                    inherits_from=json.loads(row[4]) if row[4] else None,
                    is_system_role=bool(row[5]),
                    is_assignable=bool(row[6]),
                    metadata=json.loads(row[7]) if row[7] else None
                ))

            return templates

    def create_custom_role(self, role_template: RoleTemplate) -> bool:
        """Create a custom role template."""
        if role_template.role_name in self.default_templates:
            raise ValueError(f"Cannot override system role: {role_template.role_name}")

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if role already exists
            cursor.execute(
                "SELECT role_template_id FROM role_templates WHERE role_name = %s",
                (role_template.role_name,)
            )

            if cursor.fetchone():
                raise ValueError(f"Role template already exists: {role_template.role_name}")

            try:
                template_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO role_templates
                    (role_template_id, role_name, display_name, description, permissions,
                     inherits_from, is_system_role, is_assignable, metadata, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    template_id,
                    role_template.role_name,
                    role_template.display_name,
                    role_template.description,
                    json.dumps(self._serialize_permissions(role_template.permissions)),
                    json.dumps(role_template.inherits_from) if role_template.inherits_from else None,
                    role_template.is_system_role,
                    role_template.is_assignable,
                    json.dumps(role_template.metadata) if role_template.metadata else None,
                    datetime.utcnow(),
                    datetime.utcnow()
                ))

                conn.commit()
                return True

            except Exception as e:
                print(f"Failed to create custom role: {e}")
                return False

    def resolve_role_permissions(self, role_name: str) -> Set[Permission]:
        """Resolve all permissions for a role including inheritance."""
        resolved_permissions = set()
        visited_roles = set()

        def _resolve_recursive(current_role: str):
            if current_role in visited_roles:
                return  # Avoid circular inheritance

            visited_roles.add(current_role)

            template = self.get_role_template(current_role)
            if not template:
                return

            # Add current role's permissions
            for perm in template.permissions:
                resolved_permissions.add(perm)

            # Resolve inherited permissions
            if template.inherits_from:
                for parent_role in template.inherits_from:
                    _resolve_recursive(parent_role)

        _resolve_recursive(role_name)
        return resolved_permissions

    def validate_role_hierarchy(self) -> Dict[str, List[str]]:
        """Validate role hierarchy for circular dependencies."""
        issues = {}

        for template_name in self.default_templates.keys():
            visited = set()
            path = []

            def _check_circular(role_name: str):
                if role_name in visited:
                    circular_path = path[path.index(role_name):] + [role_name]
                    return circular_path

                visited.add(role_name)
                path.append(role_name)

                template = self.get_role_template(role_name)
                if template and template.inherits_from:
                    for parent in template.inherits_from:
                        result = _check_circular(parent)
                        if result:
                            return result

                path.pop()
                return None

            circular = _check_circular(template_name)
            if circular:
                issues[template_name] = circular

        return issues

    def get_user_effective_permissions(self, user_id: str, tenant_id: str) -> Set[Permission]:
        """Get effective permissions for a user in a specific tenant."""
        effective_permissions = set()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get user's roles for the tenant
            cursor.execute("""
                SELECT rt.role_name
                FROM user_tenant_roles utr
                JOIN role_templates rt ON utr.role_template_id = rt.role_template_id
                WHERE utr.user_id = %s AND utr.tenant_id = %s AND utr.is_active = 1
            """, (user_id, tenant_id))

            roles = [row[0] for row in cursor.fetchall()]

            # Resolve permissions for each role
            for role_name in roles:
                role_permissions = self.resolve_role_permissions(role_name)
                effective_permissions.update(role_permissions)

        return effective_permissions

    def check_permission(self, user_id: str, tenant_id: str, resource: ResourceType,
                        level: PermissionLevel, conditions: Optional[Dict[str, Any]] = None) -> bool:
        """Check if user has specific permission in tenant."""
        user_permissions = self.get_user_effective_permissions(user_id, tenant_id)

        for perm in user_permissions:
            if perm.resource == resource:
                # Check permission level hierarchy
                if self._permission_level_covers(perm.level, level):
                    # Check conditions if any
                    if conditions and perm.conditions:
                        if not self._check_permission_conditions(perm.conditions, conditions):
                            continue
                    return True

        return False

    def _permission_level_covers(self, granted_level: PermissionLevel, required_level: PermissionLevel) -> bool:
        """Check if granted permission level covers required level."""
        level_hierarchy = {
            PermissionLevel.NONE: 0,
            PermissionLevel.READ_ONLY: 1,
            PermissionLevel.READ: 2,
            PermissionLevel.CREATE: 3,
            PermissionLevel.UPDATE: 4,
            PermissionLevel.DELETE: 5,
            PermissionLevel.FULL_ACCESS: 6,
            PermissionLevel.ADMIN: 7,
            PermissionLevel.SUPER_ADMIN: 8
        }

        return level_hierarchy.get(granted_level, 0) >= level_hierarchy.get(required_level, 0)

    def _check_permission_conditions(self, granted_conditions: Dict[str, Any],
                                   required_conditions: Dict[str, Any]) -> bool:
        """Check if granted conditions satisfy required conditions."""
        # Implement your condition checking logic here
        # This is a simplified example
        for key, required_value in required_conditions.items():
            granted_value = granted_conditions.get(key)
            if granted_value != required_value:
                return False
        return True