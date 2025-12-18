"""
Schema Version Manager for Multi-Tenant NLP2SQL System
Handles schema versioning, compatibility checking, and upgrade management.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from packaging import version

logger = logging.getLogger(__name__)

@dataclass
class SchemaVersionInfo:
    version: str
    release_date: str
    description: str
    breaking_changes: bool
    supported_databases: List[str]
    features: List[str]
    database_compatibility: Dict[str, Dict[str, any]]

@dataclass
class UpgradePath:
    from_version: str
    to_version: str
    supported: bool
    description: str
    migration_scripts: Dict[str, str]
    breaking_changes: bool = False
    rollback_supported: bool = False

class SchemaVersionManager:
    """
    Manages schema versions, compatibility, and upgrade paths for the
    Multi-Tenant NLP2SQL system.
    """

    def __init__(self, versions_file: str = "root_schemas/schema_versions.json"):
        """
        Initialize the Schema Version Manager.

        Args:
            versions_file: Path to the schema versions configuration file
        """
        self.versions_file = Path(versions_file)
        self.schema_registry = self._load_schema_registry()

        logger.info(f"SchemaVersionManager initialized with {len(self.schema_registry['version_history'])} versions")

    def _load_schema_registry(self) -> Dict:
        """Load schema registry from JSON file."""
        try:
            if self.versions_file.exists():
                with open(self.versions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('schema_registry', {})
            else:
                logger.warning(f"Schema versions file not found: {self.versions_file}")
                return self._create_default_registry()
        except Exception as e:
            logger.error(f"Error loading schema registry: {e}")
            return self._create_default_registry()

    def _create_default_registry(self) -> Dict:
        """Create a default schema registry."""
        return {
            "current_version": "v1.0",
            "supported_versions": ["v1.0"],
            "version_history": {},
            "upgrade_paths": {}
        }

    def get_current_version(self) -> str:
        """Get the current schema version."""
        return self.schema_registry.get('current_version', 'v1.0')

    def get_supported_versions(self) -> List[str]:
        """Get list of supported schema versions."""
        return self.schema_registry.get('supported_versions', [])

    def get_version_info(self, version: str) -> Optional[SchemaVersionInfo]:
        """
        Get detailed information about a specific schema version.

        Args:
            version: Version string (e.g., 'v1.0')

        Returns:
            SchemaVersionInfo object or None if version not found
        """
        version_data = self.schema_registry.get('version_history', {}).get(version)
        if not version_data:
            logger.warning(f"Version {version} not found in registry")
            return None

        return SchemaVersionInfo(
            version=version,
            release_date=version_data.get('release_date', ''),
            description=version_data.get('description', ''),
            breaking_changes=version_data.get('breaking_changes', False),
            supported_databases=version_data.get('supported_databases', []),
            features=version_data.get('features', []),
            database_compatibility=version_data.get('database_compatibility', {})
        )

    def is_version_supported(self, version: str) -> bool:
        """
        Check if a schema version is currently supported.

        Args:
            version: Version string to check

        Returns:
            True if version is supported, False otherwise
        """
        return version in self.get_supported_versions()

    def check_database_compatibility(self, version: str, db_type: str,
                                   db_version: str) -> Tuple[bool, str]:
        """
        Check if a database version is compatible with a schema version.

        Args:
            version: Schema version
            db_type: Database type (mysql, postgresql, etc.)
            db_version: Database server version

        Returns:
            Tuple of (is_compatible: bool, message: str)
        """
        version_info = self.get_version_info(version)
        if not version_info:
            return False, f"Schema version {version} not found"

        if db_type not in version_info.supported_databases:
            return False, f"Database type {db_type} not supported in schema {version}"

        db_compatibility = version_info.database_compatibility.get(db_type)
        if not db_compatibility:
            return False, f"No compatibility information for {db_type}"

        min_version = db_compatibility.get('min_version')
        if min_version and version.parse(db_version) < version.parse(min_version):
            return False, f"Database version {db_version} is below minimum required {min_version}"

        tested_versions = db_compatibility.get('tested_versions', [])
        if db_version not in tested_versions:
            return True, f"Database version {db_version} is compatible but not explicitly tested"

        return True, f"Database version {db_version} is fully supported"

    def get_upgrade_path(self, from_version: str, to_version: str) -> Optional[UpgradePath]:
        """
        Get upgrade path between two schema versions.

        Args:
            from_version: Source version
            to_version: Target version

        Returns:
            UpgradePath object or None if no path exists
        """
        path_key = f"{from_version}_to_{to_version}"
        upgrade_data = self.schema_registry.get('upgrade_paths', {}).get(path_key)

        if not upgrade_data:
            # Check if direct upgrade is possible
            if self._can_direct_upgrade(from_version, to_version):
                return UpgradePath(
                    from_version=from_version,
                    to_version=to_version,
                    supported=True,
                    description=f"Direct upgrade from {from_version} to {to_version}",
                    migration_scripts=self._get_default_migration_scripts(from_version, to_version)
                )
            return None

        return UpgradePath(
            from_version=from_version,
            to_version=to_version,
            supported=upgrade_data.get('supported', False),
            description=upgrade_data.get('description', ''),
            migration_scripts=upgrade_data.get('migration_scripts', {}),
            breaking_changes=upgrade_data.get('breaking_changes', False),
            rollback_supported=upgrade_data.get('rollback_supported', False)
        )

    def find_upgrade_chain(self, from_version: str, to_version: str) -> List[UpgradePath]:
        """
        Find a chain of upgrade paths to get from one version to another.

        Args:
            from_version: Source version
            to_version: Target version

        Returns:
            List of UpgradePath objects representing the upgrade chain
        """
        # Simple implementation - can be enhanced with graph algorithms
        # for complex upgrade scenarios
        direct_path = self.get_upgrade_path(from_version, to_version)
        if direct_path and direct_path.supported:
            return [direct_path]

        # For now, only support direct upgrades
        # Future enhancement: implement multi-step upgrade paths
        return []

    def validate_upgrade_feasibility(self, from_version: str, to_version: str,
                                   db_type: str) -> Tuple[bool, List[str]]:
        """
        Validate if an upgrade is feasible.

        Args:
            from_version: Source version
            to_version: Target version
            db_type: Database type

        Returns:
            Tuple of (is_feasible: bool, issues: List[str])
        """
        issues = []

        # Check if source version is supported
        if not self.is_version_supported(from_version):
            issues.append(f"Source version {from_version} is not supported")

        # Check if target version exists
        target_info = self.get_version_info(to_version)
        if not target_info:
            issues.append(f"Target version {to_version} does not exist")
            return False, issues

        # Check if database type is supported in target version
        if db_type not in target_info.supported_databases:
            issues.append(f"Database type {db_type} not supported in version {to_version}")

        # Check if upgrade path exists
        upgrade_path = self.get_upgrade_path(from_version, to_version)
        if not upgrade_path or not upgrade_path.supported:
            issues.append(f"No supported upgrade path from {from_version} to {to_version}")

        # Check for breaking changes
        if upgrade_path and upgrade_path.breaking_changes:
            issues.append(f"Upgrade contains breaking changes - manual intervention may be required")

        # Check if migration script exists for database type
        if upgrade_path and db_type not in upgrade_path.migration_scripts:
            issues.append(f"No migration script available for {db_type}")

        is_feasible = len(issues) == 0

        if is_feasible:
            logger.info(f"Upgrade from {from_version} to {to_version} for {db_type} is feasible")
        else:
            logger.warning(f"Upgrade validation failed: {'; '.join(issues)}")

        return is_feasible, issues

    def get_version_changelog(self, from_version: str = None, to_version: str = None) -> List[Dict]:
        """
        Get changelog between versions.

        Args:
            from_version: Starting version (optional, defaults to first version)
            to_version: Ending version (optional, defaults to current version)

        Returns:
            List of version changes
        """
        changelog = []
        versions = sorted(self.schema_registry.get('version_history', {}).keys(),
                         key=lambda v: version.parse(v.lstrip('v')))

        start_idx = 0
        end_idx = len(versions)

        if from_version:
            try:
                start_idx = versions.index(from_version)
            except ValueError:
                logger.warning(f"From version {from_version} not found")

        if to_version:
            try:
                end_idx = versions.index(to_version) + 1
            except ValueError:
                logger.warning(f"To version {to_version} not found")

        for ver in versions[start_idx:end_idx]:
            version_info = self.get_version_info(ver)
            if version_info:
                changelog.append({
                    'version': ver,
                    'release_date': version_info.release_date,
                    'description': version_info.description,
                    'features': version_info.features,
                    'breaking_changes': version_info.breaking_changes
                })

        return changelog

    def register_new_version(self, version: str, version_info: SchemaVersionInfo,
                           upgrade_paths: List[UpgradePath] = None) -> bool:
        """
        Register a new schema version in the registry.

        Args:
            version: Version string
            version_info: Version information
            upgrade_paths: Optional upgrade paths from this version

        Returns:
            True if registration was successful
        """
        try:
            # Add version to history
            self.schema_registry['version_history'][version] = {
                'release_date': version_info.release_date,
                'description': version_info.description,
                'breaking_changes': version_info.breaking_changes,
                'supported_databases': version_info.supported_databases,
                'features': version_info.features,
                'database_compatibility': version_info.database_compatibility
            }

            # Add upgrade paths
            if upgrade_paths:
                for path in upgrade_paths:
                    path_key = f"{path.from_version}_to_{path.to_version}"
                    self.schema_registry['upgrade_paths'][path_key] = {
                        'supported': path.supported,
                        'description': path.description,
                        'migration_scripts': path.migration_scripts,
                        'breaking_changes': path.breaking_changes,
                        'rollback_supported': path.rollback_supported
                    }

            # Update supported versions
            if version not in self.schema_registry['supported_versions']:
                self.schema_registry['supported_versions'].append(version)

            # Save registry
            self._save_schema_registry()

            logger.info(f"Successfully registered schema version {version}")
            return True

        except Exception as e:
            logger.error(f"Error registering version {version}: {e}")
            return False

    def deprecate_version(self, version: str, reason: str = None) -> bool:
        """
        Deprecate a schema version.

        Args:
            version: Version to deprecate
            reason: Optional reason for deprecation

        Returns:
            True if deprecation was successful
        """
        try:
            if version in self.schema_registry.get('supported_versions', []):
                self.schema_registry['supported_versions'].remove(version)

            # Add deprecation info
            if version in self.schema_registry.get('version_history', {}):
                self.schema_registry['version_history'][version]['deprecated'] = True
                self.schema_registry['version_history'][version]['deprecation_reason'] = reason
                self.schema_registry['version_history'][version]['deprecated_date'] = datetime.now().isoformat()

            self._save_schema_registry()

            logger.info(f"Successfully deprecated schema version {version}")
            return True

        except Exception as e:
            logger.error(f"Error deprecating version {version}: {e}")
            return False

    def _can_direct_upgrade(self, from_version: str, to_version: str) -> bool:
        """Check if direct upgrade is possible between versions."""
        try:
            from_ver = version.parse(from_version.lstrip('v'))
            to_ver = version.parse(to_version.lstrip('v'))

            # Allow upgrade if target version is newer
            return to_ver > from_ver
        except Exception:
            return False

    def _get_default_migration_scripts(self, from_version: str, to_version: str) -> Dict[str, str]:
        """Get default migration script paths."""
        return {
            'mysql': f"migrations/mysql/migrate_{from_version}_to_{to_version}.sql",
            'postgresql': f"migrations/postgresql/migrate_{from_version}_to_{to_version}.sql",
            'sqlite': f"migrations/sqlite/migrate_{from_version}_to_{to_version}.sql",
            'mongodb': f"migrations/mongodb/migrate_{from_version}_to_{to_version}.json"
        }

    def _save_schema_registry(self) -> bool:
        """Save schema registry to file."""
        try:
            registry_data = {
                'schema_registry': self.schema_registry,
                'updated_at': datetime.now().isoformat()
            }

            with open(self.versions_file, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error(f"Error saving schema registry: {e}")
            return False