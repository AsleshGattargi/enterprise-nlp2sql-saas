"""
Port Management System for Database Cloning Engine
Handles automatic port allocation and management for tenant database containers.
"""

import json
import logging
import socket
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .root_image_manager import DatabaseType

logger = logging.getLogger(__name__)

@dataclass
class PortAllocation:
    database_type: DatabaseType
    port: int
    tenant_id: Optional[str] = None
    container_id: Optional[str] = None
    allocated_at: str = None
    is_active: bool = True

class PortManager:
    """
    Manages port allocation for tenant database containers.
    Ensures no port conflicts and provides automatic assignment.
    """

    def __init__(self, config_file: str = "port_config.json"):
        """
        Initialize Port Manager.

        Args:
            config_file: Configuration file for port settings
        """
        self.config_file = Path(config_file)

        # Default port ranges for each database type
        self.port_ranges = {
            DatabaseType.MYSQL: (3309, 3400),      # Starting from 3309 (3307-3308 used by existing)
            DatabaseType.POSTGRESQL: (5434, 5500), # Starting from 5434 (5433 used by existing)
            DatabaseType.MONGODB: (27019, 27100),  # Starting from 27019 (27018 used by existing)
            DatabaseType.SQLITE: (None, None)      # SQLite doesn't need ports
        }

        # Reserved ports that should not be allocated
        self.reserved_ports = {
            3306, 3307, 3308,  # Existing MySQL instances
            5432, 5433,        # Existing PostgreSQL instances
            27017, 27018,      # Existing MongoDB instances
            8000, 8001,        # FastAPI
            8501,              # Streamlit
            8080, 8081, 8082   # Admin tools
        }

        # Current port allocations
        self.allocations: Dict[int, PortAllocation] = {}

        # Load existing allocations
        self._load_allocations()

        logger.info("PortManager initialized successfully")

    def allocate_port(self, database_type: DatabaseType,
                     tenant_id: str = None, preferred_port: int = None) -> Optional[int]:
        """
        Allocate a free port for the specified database type.

        Args:
            database_type: Database type requiring port
            tenant_id: Optional tenant identifier
            preferred_port: Preferred port number (if available)

        Returns:
            Allocated port number or None if no ports available
        """
        try:
            if database_type == DatabaseType.SQLITE:
                logger.debug("SQLite doesn't require port allocation")
                return None

            logger.info(f"Allocating port for {database_type.value} (tenant: {tenant_id})")

            # Check if preferred port is available
            if preferred_port and self._is_port_available(preferred_port, database_type):
                return self._allocate_specific_port(preferred_port, database_type, tenant_id)

            # Find next available port in range
            start_port, end_port = self.port_ranges[database_type]

            for port in range(start_port, end_port + 1):
                if self._is_port_available(port, database_type):
                    return self._allocate_specific_port(port, database_type, tenant_id)

            logger.error(f"No available ports for {database_type.value}")
            return None

        except Exception as e:
            logger.error(f"Port allocation failed: {e}")
            return None

    def release_port(self, database_type: DatabaseType, port: int) -> bool:
        """
        Release an allocated port.

        Args:
            database_type: Database type
            port: Port number to release

        Returns:
            True if port was released successfully
        """
        try:
            if database_type == DatabaseType.SQLITE:
                return True

            if port not in self.allocations:
                logger.warning(f"Port {port} not found in allocations")
                return True

            allocation = self.allocations[port]
            if allocation.database_type != database_type:
                logger.error(f"Port {port} allocated for different database type")
                return False

            # Mark as inactive instead of removing to maintain history
            allocation.is_active = False

            self._save_allocations()

            logger.info(f"Released port {port} for {database_type.value}")
            return True

        except Exception as e:
            logger.error(f"Port release failed: {e}")
            return False

    def get_allocated_ports(self, database_type: DatabaseType = None,
                           active_only: bool = True) -> List[PortAllocation]:
        """
        Get list of allocated ports.

        Args:
            database_type: Filter by database type (optional)
            active_only: Only return active allocations

        Returns:
            List of port allocations
        """
        allocations = list(self.allocations.values())

        if active_only:
            allocations = [a for a in allocations if a.is_active]

        if database_type:
            allocations = [a for a in allocations if a.database_type == database_type]

        return sorted(allocations, key=lambda x: x.port)

    def get_port_for_tenant(self, tenant_id: str) -> Optional[PortAllocation]:
        """
        Get port allocation for a specific tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Port allocation or None if not found
        """
        for allocation in self.allocations.values():
            if allocation.tenant_id == tenant_id and allocation.is_active:
                return allocation
        return None

    def is_port_in_use(self, port: int) -> bool:
        """
        Check if a port is currently in use by the system.

        Args:
            port: Port number to check

        Returns:
            True if port is in use
        """
        try:
            # Check if port is allocated in our system
            if port in self.allocations and self.allocations[port].is_active:
                return True

            # Check if port is actually bound on the system
            return not self._check_port_available_on_system(port)

        except Exception as e:
            logger.error(f"Error checking port {port}: {e}")
            return True  # Assume in use if we can't check

    def get_next_available_port(self, database_type: DatabaseType,
                               start_from: int = None) -> Optional[int]:
        """
        Get the next available port for a database type.

        Args:
            database_type: Database type
            start_from: Starting port number (optional)

        Returns:
            Next available port or None
        """
        if database_type == DatabaseType.SQLITE:
            return None

        start_port, end_port = self.port_ranges[database_type]

        if start_from and start_from >= start_port:
            search_start = start_from
        else:
            search_start = start_port

        for port in range(search_start, end_port + 1):
            if self._is_port_available(port, database_type):
                return port

        return None

    def update_port_allocation(self, port: int, tenant_id: str = None,
                              container_id: str = None) -> bool:
        """
        Update port allocation with additional information.

        Args:
            port: Port number
            tenant_id: Tenant identifier
            container_id: Container identifier

        Returns:
            True if updated successfully
        """
        try:
            if port not in self.allocations:
                logger.error(f"Port {port} not found in allocations")
                return False

            allocation = self.allocations[port]

            if tenant_id:
                allocation.tenant_id = tenant_id

            if container_id:
                allocation.container_id = container_id

            self._save_allocations()

            logger.info(f"Updated port allocation for port {port}")
            return True

        except Exception as e:
            logger.error(f"Failed to update port allocation: {e}")
            return False

    def cleanup_inactive_allocations(self, max_age_hours: int = 24) -> int:
        """
        Cleanup old inactive port allocations.

        Args:
            max_age_hours: Maximum age for inactive allocations

        Returns:
            Number of allocations cleaned up
        """
        try:
            from datetime import datetime, timedelta

            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cleaned_count = 0

            ports_to_remove = []

            for port, allocation in self.allocations.items():
                if not allocation.is_active and allocation.allocated_at:
                    try:
                        allocated_time = datetime.fromisoformat(allocation.allocated_at)
                        if allocated_time < cutoff_time:
                            ports_to_remove.append(port)
                            cleaned_count += 1
                    except ValueError:
                        # Invalid timestamp, remove it
                        ports_to_remove.append(port)
                        cleaned_count += 1

            # Remove old allocations
            for port in ports_to_remove:
                del self.allocations[port]

            if cleaned_count > 0:
                self._save_allocations()
                logger.info(f"Cleaned up {cleaned_count} inactive port allocations")

            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup allocations: {e}")
            return 0

    def get_port_statistics(self) -> Dict[str, any]:
        """
        Get port allocation statistics.

        Returns:
            Statistics dictionary
        """
        try:
            stats = {
                'total_allocations': len(self.allocations),
                'active_allocations': len([a for a in self.allocations.values() if a.is_active]),
                'inactive_allocations': len([a for a in self.allocations.values() if not a.is_active]),
                'by_database_type': {},
                'port_ranges': {}
            }

            # Stats by database type
            for db_type in DatabaseType:
                if db_type == DatabaseType.SQLITE:
                    continue

                active_count = len([a for a in self.allocations.values()
                                  if a.database_type == db_type and a.is_active])
                total_count = len([a for a in self.allocations.values()
                                 if a.database_type == db_type])

                start_port, end_port = self.port_ranges[db_type]
                available_ports = end_port - start_port + 1

                stats['by_database_type'][db_type.value] = {
                    'active_allocations': active_count,
                    'total_allocations': total_count,
                    'available_ports': available_ports,
                    'utilization_percent': (active_count / available_ports) * 100
                }

            # Port range info
            for db_type, (start, end) in self.port_ranges.items():
                if db_type == DatabaseType.SQLITE:
                    continue
                stats['port_ranges'][db_type.value] = {
                    'start': start,
                    'end': end,
                    'total': end - start + 1 if start and end else 0
                }

            return stats

        except Exception as e:
            logger.error(f"Failed to get port statistics: {e}")
            return {}

    def configure_port_ranges(self, ranges: Dict[str, Tuple[int, int]]) -> bool:
        """
        Configure custom port ranges for database types.

        Args:
            ranges: Dictionary of database_type -> (start_port, end_port)

        Returns:
            True if configuration was successful
        """
        try:
            for db_type_str, (start, end) in ranges.items():
                try:
                    db_type = DatabaseType(db_type_str.lower())
                    if db_type != DatabaseType.SQLITE:
                        self.port_ranges[db_type] = (start, end)
                        logger.info(f"Updated port range for {db_type.value}: {start}-{end}")
                except ValueError:
                    logger.warning(f"Invalid database type: {db_type_str}")

            self._save_config()
            return True

        except Exception as e:
            logger.error(f"Failed to configure port ranges: {e}")
            return False

    def export_allocations(self, file_path: str = None) -> str:
        """
        Export current port allocations to JSON.

        Args:
            file_path: Optional file path to save to

        Returns:
            JSON string of allocations
        """
        try:
            export_data = {
                'port_ranges': {db_type.value: range_tuple
                               for db_type, range_tuple in self.port_ranges.items()
                               if range_tuple != (None, None)},
                'allocations': {str(port): {
                    'database_type': allocation.database_type.value,
                    'tenant_id': allocation.tenant_id,
                    'container_id': allocation.container_id,
                    'allocated_at': allocation.allocated_at,
                    'is_active': allocation.is_active
                } for port, allocation in self.allocations.items()},
                'reserved_ports': list(self.reserved_ports)
            }

            json_data = json.dumps(export_data, indent=2)

            if file_path:
                with open(file_path, 'w') as f:
                    f.write(json_data)
                logger.info(f"Port allocations exported to: {file_path}")

            return json_data

        except Exception as e:
            logger.error(f"Failed to export allocations: {e}")
            return "{}"

    # Private helper methods

    def _is_port_available(self, port: int, database_type: DatabaseType) -> bool:
        """Check if a port is available for allocation."""
        # Check if port is reserved
        if port in self.reserved_ports:
            return False

        # Check if port is already allocated and active
        if port in self.allocations and self.allocations[port].is_active:
            return False

        # Check if port is in valid range for database type
        start_port, end_port = self.port_ranges[database_type]
        if not (start_port <= port <= end_port):
            return False

        # Check if port is actually available on the system
        return self._check_port_available_on_system(port)

    def _check_port_available_on_system(self, port: int) -> bool:
        """Check if port is available on the system."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                result = sock.bind(('localhost', port))
                return True
        except socket.error:
            return False

    def _allocate_specific_port(self, port: int, database_type: DatabaseType,
                               tenant_id: str = None) -> int:
        """Allocate a specific port."""
        from datetime import datetime

        allocation = PortAllocation(
            database_type=database_type,
            port=port,
            tenant_id=tenant_id,
            allocated_at=datetime.now().isoformat(),
            is_active=True
        )

        self.allocations[port] = allocation
        self._save_allocations()

        logger.info(f"Allocated port {port} for {database_type.value}")
        return port

    def _load_allocations(self):
        """Load port allocations from persistent storage."""
        try:
            allocations_file = Path("port_allocations.json")
            if allocations_file.exists():
                with open(allocations_file, 'r') as f:
                    data = json.load(f)

                for port_str, allocation_data in data.get('allocations', {}).items():
                    port = int(port_str)
                    allocation_data['database_type'] = DatabaseType(allocation_data['database_type'])
                    allocation_data['port'] = port

                    self.allocations[port] = PortAllocation(**allocation_data)

                # Load custom port ranges if available
                if 'port_ranges' in data:
                    for db_type_str, range_tuple in data['port_ranges'].items():
                        db_type = DatabaseType(db_type_str)
                        self.port_ranges[db_type] = tuple(range_tuple)

                # Load reserved ports if available
                if 'reserved_ports' in data:
                    self.reserved_ports.update(data['reserved_ports'])

                logger.info(f"Loaded {len(self.allocations)} port allocations")

        except Exception as e:
            logger.warning(f"Failed to load port allocations: {e}")

    def _save_allocations(self):
        """Save port allocations to persistent storage."""
        try:
            data = {
                'allocations': {},
                'port_ranges': {},
                'reserved_ports': list(self.reserved_ports)
            }

            # Convert allocations to JSON-serializable format
            for port, allocation in self.allocations.items():
                data['allocations'][str(port)] = {
                    'database_type': allocation.database_type.value,
                    'port': allocation.port,
                    'tenant_id': allocation.tenant_id,
                    'container_id': allocation.container_id,
                    'allocated_at': allocation.allocated_at,
                    'is_active': allocation.is_active
                }

            # Save port ranges
            for db_type, range_tuple in self.port_ranges.items():
                if range_tuple != (None, None):
                    data['port_ranges'][db_type.value] = range_tuple

            allocations_file = Path("port_allocations.json")
            with open(allocations_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save port allocations: {e}")

    def _save_config(self):
        """Save port manager configuration."""
        try:
            config = {
                'port_ranges': {db_type.value: range_tuple
                               for db_type, range_tuple in self.port_ranges.items()
                               if range_tuple != (None, None)},
                'reserved_ports': list(self.reserved_ports)
            }

            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info("Port manager configuration saved")

        except Exception as e:
            logger.error(f"Failed to save port manager config: {e}")

    def _load_config(self):
        """Load port manager configuration."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)

                # Load port ranges
                if 'port_ranges' in config:
                    for db_type_str, range_tuple in config['port_ranges'].items():
                        db_type = DatabaseType(db_type_str)
                        self.port_ranges[db_type] = tuple(range_tuple)

                # Load reserved ports
                if 'reserved_ports' in config:
                    self.reserved_ports.update(config['reserved_ports'])

                logger.info("Port manager configuration loaded")

        except Exception as e:
            logger.warning(f"Failed to load port manager config: {e}")