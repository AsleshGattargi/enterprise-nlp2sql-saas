#!/usr/bin/env python3
"""
Database Cloning Manager CLI
Command-line interface for managing tenant database clones.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

from src.database_cloner import DatabaseCloner, CloneStatus
from src.clone_verifier import CloneVerifier
from src.port_manager import PortManager
from src.docker_manager import DockerManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CloneManagerCLI:
    """Command-line interface for database cloning management."""

    def __init__(self):
        self.database_cloner = DatabaseCloner()
        self.clone_verifier = CloneVerifier()
        self.port_manager = PortManager()
        self.docker_manager = DockerManager()

    def create_clone(self, args):
        """Create a new tenant clone."""
        try:
            print(f"🔄 Creating clone for tenant: {args.tenant_id}")
            print(f"Database type: {args.db_type}")
            print(f"Root version: {args.version or 'latest'}")

            # Parse custom config if provided
            custom_config = None
            if args.config:
                with open(args.config, 'r') as f:
                    custom_config = json.load(f)

            success, message, clone = self.database_cloner.clone_from_root(
                tenant_id=args.tenant_id,
                db_type=args.db_type,
                root_version=args.version,
                custom_config=custom_config
            )

            if success:
                print(f"✅ Clone created successfully!")
                print(f"   Clone ID: {clone.clone_id}")
                print(f"   Database: {clone.database_name}")
                if clone.port:
                    print(f"   Port: {clone.port}")
                if clone.container_id:
                    print(f"   Container: {clone.container_id[:12]}")

                return 0
            else:
                print(f"❌ Clone creation failed: {message}")
                return 1

        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def verify_clone(self, args):
        """Verify tenant clone isolation."""
        try:
            print(f"🔍 Verifying isolation for tenant: {args.tenant_id}")

            result = self.database_cloner.verify_clone_isolation(args.tenant_id)

            print(f"\n📊 Verification Results:")
            print(f"Overall Status: {'✅ VERIFIED' if result.is_verified else '❌ FAILED'}")
            print(f"Checks Passed: {result.checks_passed}/{result.total_checks}")
            print(f"Connection Test: {'✅ PASS' if result.connection_test else '❌ FAIL'}")
            print(f"Schema Integrity: {'✅ PASS' if result.schema_integrity else '❌ FAIL'}")
            print(f"Isolation Verified: {'✅ PASS' if result.isolation_verified else '❌ FAIL'}")

            if result.isolation_tests:
                print(f"\n🔍 Detailed Test Results:")
                for test in result.isolation_tests:
                    status = "✅" if test.passed else "❌"
                    print(f"   {status} {test.test_name}: {test.details} ({test.execution_time_ms}ms)")

            if result.error_messages:
                print(f"\n❌ Errors:")
                for error in result.error_messages:
                    print(f"   • {error}")

            return 0 if result.is_verified else 1

        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def list_clones(self, args):
        """List tenant clones."""
        try:
            clones = self.database_cloner.list_tenant_clones(args.tenant_id)

            if not clones:
                if args.tenant_id:
                    print(f"No clones found for tenant: {args.tenant_id}")
                else:
                    print("No clones found.")
                return 0

            print(f"\n📋 Found {len(clones)} clone(s):")
            print("-" * 80)

            for clone in clones:
                status_icon = self._get_status_icon(clone.status)
                print(f"{status_icon} {clone.tenant_id} ({clone.database_type.value})")
                print(f"   Clone ID: {clone.clone_id}")
                print(f"   Database: {clone.database_name}")
                print(f"   Status: {clone.status.value}")
                print(f"   Version: {clone.root_version}")

                if clone.port:
                    print(f"   Port: {clone.port}")

                if clone.container_id:
                    print(f"   Container: {clone.container_id[:12]}")

                print(f"   Created: {clone.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

                if clone.completed_at:
                    print(f"   Completed: {clone.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")

                if clone.error_message:
                    print(f"   Error: {clone.error_message}")

                print()

            return 0

        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def remove_clone(self, args):
        """Remove a tenant clone."""
        try:
            if not args.force:
                confirm = input(f"Remove clone for tenant '{args.tenant_id}'? (y/N): ")
                if confirm.lower() != 'y':
                    print("Operation cancelled.")
                    return 0

            print(f"🗑️ Removing clone for tenant: {args.tenant_id}")

            success = self.database_cloner.remove_tenant_clone(args.tenant_id, force=True)

            if success:
                print("✅ Clone removed successfully!")
                return 0
            else:
                print("❌ Failed to remove clone.")
                return 1

        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def start_database(self, args):
        """Start tenant database."""
        try:
            print(f"▶️ Starting database for tenant: {args.tenant_id}")

            success = self.database_cloner.start_tenant_database(args.tenant_id)

            if success:
                print("✅ Database started successfully!")
                return 0
            else:
                print("❌ Failed to start database.")
                return 1

        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def stop_database(self, args):
        """Stop tenant database."""
        try:
            print(f"⏹️ Stopping database for tenant: {args.tenant_id}")

            success = self.database_cloner.stop_tenant_database(args.tenant_id)

            if success:
                print("✅ Database stopped successfully!")
                return 0
            else:
                print("❌ Failed to stop database.")
                return 1

        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def show_status(self, args):
        """Show system status."""
        try:
            print("📊 Database Cloning System Status")
            print("=" * 40)

            # Clone statistics
            all_clones = self.database_cloner.list_tenant_clones()
            total_clones = len(all_clones)
            active_clones = len([c for c in all_clones if c.status == CloneStatus.COMPLETED])
            failed_clones = len([c for c in all_clones if c.status == CloneStatus.FAILED])

            print(f"Total Clones: {total_clones}")
            print(f"Active Clones: {active_clones}")
            print(f"Failed Clones: {failed_clones}")

            # Port statistics
            port_stats = self.port_manager.get_port_statistics()
            if port_stats:
                print(f"\nPort Allocations:")
                print(f"Active Allocations: {port_stats['active_allocations']}")
                print(f"Total Allocations: {port_stats['total_allocations']}")

                for db_type, stats in port_stats.get('by_database_type', {}).items():
                    print(f"  {db_type}: {stats['active_allocations']} active, {stats['utilization_percent']:.1f}% utilization")

            # Docker system info
            docker_info = self.docker_manager.get_system_info()
            if docker_info:
                print(f"\nDocker System:")
                print(f"Running Containers: {docker_info.get('containers_running', 0)}")
                print(f"Paused Containers: {docker_info.get('containers_paused', 0)}")
                print(f"Stopped Containers: {docker_info.get('containers_stopped', 0)}")
                print(f"Docker Version: {docker_info.get('docker_version', 'unknown')}")

            return 0

        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def test_system(self, args):
        """Run system tests."""
        try:
            print("🧪 Running Database Cloning System Tests")
            print("=" * 50)

            # Import and run the test suite
            from test_database_cloning import DatabaseCloningTestSuite

            async def run_tests():
                test_suite = DatabaseCloningTestSuite()
                results = await test_suite.run_comprehensive_tests()

                if args.cleanup:
                    await test_suite.cleanup_test_resources()

                return results

            results = asyncio.run(run_tests())

            print(f"\n🎯 Test Results Summary:")
            print(f"Total Tests: {results['total_tests']}")
            print(f"Passed: {results['passed_tests']}")
            print(f"Failed: {results['failed_tests']}")

            if results['passed_tests'] == results['total_tests']:
                print("🎉 All tests passed!")
                return 0
            else:
                print("⚠️ Some tests failed. Check test_report_database_cloning.json for details.")
                return 1

        except Exception as e:
            print(f"❌ Error: {e}")
            return 1

    def _get_status_icon(self, status):
        """Get icon for clone status."""
        icons = {
            CloneStatus.PENDING: "⏳",
            CloneStatus.IN_PROGRESS: "🔄",
            CloneStatus.COMPLETED: "✅",
            CloneStatus.FAILED: "❌",
            CloneStatus.CLEANING_UP: "🧹",
            CloneStatus.REMOVED: "🗑️"
        }
        return icons.get(status, "❓")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database Cloning Manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create tenant_001 mysql --version v1.0
  %(prog)s verify tenant_001
  %(prog)s list
  %(prog)s remove tenant_001 --force
  %(prog)s status
        """
    )

    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new tenant clone')
    create_parser.add_argument('tenant_id', help='Tenant ID')
    create_parser.add_argument('db_type', choices=['mysql', 'postgresql', 'sqlite', 'mongodb'],
                              help='Database type')
    create_parser.add_argument('--version', help='Root schema version (default: latest)')
    create_parser.add_argument('--config', help='Custom configuration JSON file')

    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify tenant clone isolation')
    verify_parser.add_argument('tenant_id', help='Tenant ID')

    # List command
    list_parser = subparsers.add_parser('list', help='List tenant clones')
    list_parser.add_argument('--tenant-id', help='Filter by tenant ID')

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a tenant clone')
    remove_parser.add_argument('tenant_id', help='Tenant ID')
    remove_parser.add_argument('--force', action='store_true', help='Force removal without confirmation')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start tenant database')
    start_parser.add_argument('tenant_id', help='Tenant ID')

    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop tenant database')
    stop_parser.add_argument('tenant_id', help='Tenant ID')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')

    # Test command
    test_parser = subparsers.add_parser('test', help='Run system tests')
    test_parser.add_argument('--cleanup', action='store_true', help='Cleanup test resources after testing')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.command:
        parser.print_help()
        return 1

    cli = CloneManagerCLI()

    # Execute command
    command_methods = {
        'create': cli.create_clone,
        'verify': cli.verify_clone,
        'list': cli.list_clones,
        'remove': cli.remove_clone,
        'start': cli.start_database,
        'stop': cli.stop_database,
        'status': cli.show_status,
        'test': cli.test_system
    }

    if args.command in command_methods:
        return command_methods[args.command](args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())