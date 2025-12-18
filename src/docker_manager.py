"""
Docker Container Management for Database Cloning Engine
Handles Docker container lifecycle, networking, and volume management.
"""

import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

import docker
from docker.client import DockerClient
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.volumes import Volume
from docker.models.networks import Network
from docker.errors import DockerException, NotFound, APIError

logger = logging.getLogger(__name__)

class DockerManager:
    """
    Manages Docker containers for tenant database cloning.
    Handles container creation, lifecycle management, and networking.
    """

    def __init__(self, docker_url: str = None):
        """
        Initialize Docker Manager.

        Args:
            docker_url: Docker daemon URL (defaults to local daemon)
        """
        try:
            if docker_url:
                self.client = docker.DockerClient(base_url=docker_url)
            else:
                self.client = docker.from_env()

            # Test Docker connection
            self.client.ping()
            logger.info("Docker Manager initialized successfully")

            # Create tenant network if it doesn't exist
            self._ensure_tenant_network()

        except Exception as e:
            logger.error(f"Failed to initialize Docker Manager: {e}")
            raise

    def create_container(self, image: str, name: str, ports: Dict[str, int],
                        environment: Dict[str, str], volumes: Dict[str, Dict] = None,
                        network: str = "nlp2sql_tenant_network",
                        **kwargs) -> Optional[Container]:
        """
        Create a new Docker container.

        Args:
            image: Docker image name
            name: Container name
            ports: Port mapping {container_port: host_port}
            environment: Environment variables
            volumes: Volume mounts
            network: Network to attach container to
            **kwargs: Additional container options

        Returns:
            Container object or None if creation failed
        """
        try:
            logger.info(f"Creating container: {name}")

            # Ensure image is available
            self._ensure_image(image)

            # Prepare port configuration
            port_bindings = {}
            exposed_ports = []

            for container_port, host_port in ports.items():
                port_bindings[container_port] = host_port
                exposed_ports.append(container_port)

            # Create container
            container = self.client.containers.create(
                image=image,
                name=name,
                ports=port_bindings,
                environment=environment,
                volumes=volumes or {},
                network=network,
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                **kwargs
            )

            logger.info(f"Container created successfully: {name} ({container.id[:12]})")
            return container

        except Exception as e:
            logger.error(f"Failed to create container {name}: {e}")
            return None

    def start_container(self, container_id: str) -> bool:
        """
        Start a Docker container.

        Args:
            container_id: Container ID or name

        Returns:
            True if started successfully
        """
        try:
            container = self.client.containers.get(container_id)
            container.start()

            logger.info(f"Container started: {container_id}")
            return True

        except NotFound:
            logger.error(f"Container not found: {container_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to start container {container_id}: {e}")
            return False

    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """
        Stop a Docker container.

        Args:
            container_id: Container ID or name
            timeout: Timeout for graceful shutdown

        Returns:
            True if stopped successfully
        """
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)

            logger.info(f"Container stopped: {container_id}")
            return True

        except NotFound:
            logger.error(f"Container not found: {container_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to stop container {container_id}: {e}")
            return False

    def remove_container(self, container_id: str, force: bool = False,
                        remove_volumes: bool = True) -> bool:
        """
        Remove a Docker container.

        Args:
            container_id: Container ID or name
            force: Force removal even if running
            remove_volumes: Remove associated volumes

        Returns:
            True if removed successfully
        """
        try:
            container = self.client.containers.get(container_id)

            # Stop container if running and force is True
            if container.status == 'running' and force:
                self.stop_container(container_id)

            container.remove(v=remove_volumes)

            logger.info(f"Container removed: {container_id}")
            return True

        except NotFound:
            logger.warning(f"Container not found (already removed?): {container_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove container {container_id}: {e}")
            return False

    def restart_container(self, container_id: str, timeout: int = 10) -> bool:
        """
        Restart a Docker container.

        Args:
            container_id: Container ID or name
            timeout: Timeout for graceful shutdown

        Returns:
            True if restarted successfully
        """
        try:
            container = self.client.containers.get(container_id)
            container.restart(timeout=timeout)

            logger.info(f"Container restarted: {container_id}")
            return True

        except NotFound:
            logger.error(f"Container not found: {container_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to restart container {container_id}: {e}")
            return False

    def is_container_running(self, container_id: str) -> bool:
        """
        Check if a container is running.

        Args:
            container_id: Container ID or name

        Returns:
            True if container is running
        """
        try:
            container = self.client.containers.get(container_id)
            return container.status == 'running'

        except NotFound:
            return False
        except Exception as e:
            logger.error(f"Failed to check container status {container_id}: {e}")
            return False

    def get_container_info(self, container_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed container information.

        Args:
            container_id: Container ID or name

        Returns:
            Container information dictionary or None
        """
        try:
            container = self.client.containers.get(container_id)
            container.reload()

            info = {
                'id': container.id,
                'name': container.name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else container.image.id,
                'created': container.attrs['Created'],
                'ports': container.attrs['NetworkSettings']['Ports'],
                'environment': container.attrs['Config']['Env'],
                'mounts': container.attrs['Mounts']
            }

            return info

        except NotFound:
            logger.error(f"Container not found: {container_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get container info {container_id}: {e}")
            return None

    def list_tenant_containers(self, tenant_prefix: str = None) -> List[Dict[str, Any]]:
        """
        List all tenant containers.

        Args:
            tenant_prefix: Optional prefix filter for container names

        Returns:
            List of container information dictionaries
        """
        try:
            containers = []
            all_containers = self.client.containers.list(all=True)

            for container in all_containers:
                # Filter by tenant prefix if specified
                if tenant_prefix and not container.name.startswith(tenant_prefix):
                    continue

                # Only include containers that look like tenant containers
                if any(db_type in container.name for db_type in ['mysql', 'postgresql', 'mongodb']):
                    info = {
                        'id': container.id,
                        'name': container.name,
                        'status': container.status,
                        'image': container.image.tags[0] if container.image.tags else container.image.id,
                        'created': container.attrs['Created']
                    }
                    containers.append(info)

            return containers

        except Exception as e:
            logger.error(f"Failed to list tenant containers: {e}")
            return []

    def get_container_logs(self, container_id: str, lines: int = 100,
                          since: str = None) -> Optional[str]:
        """
        Get container logs.

        Args:
            container_id: Container ID or name
            lines: Number of lines to retrieve
            since: Retrieve logs since timestamp

        Returns:
            Container logs as string or None
        """
        try:
            container = self.client.containers.get(container_id)

            logs_kwargs = {
                'tail': lines,
                'timestamps': True
            }

            if since:
                logs_kwargs['since'] = since

            logs = container.logs(**logs_kwargs)
            return logs.decode('utf-8')

        except NotFound:
            logger.error(f"Container not found: {container_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get container logs {container_id}: {e}")
            return None

    def execute_command(self, container_id: str, command: str,
                       user: str = None) -> Tuple[bool, str, str]:
        """
        Execute a command inside a container.

        Args:
            container_id: Container ID or name
            command: Command to execute
            user: User to run command as

        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            container = self.client.containers.get(container_id)

            exec_kwargs = {
                'cmd': command,
                'stdout': True,
                'stderr': True
            }

            if user:
                exec_kwargs['user'] = user

            exec_result = container.exec_run(**exec_kwargs)

            success = exec_result.exit_code == 0
            stdout = exec_result.output.decode('utf-8') if exec_result.output else ""

            logger.info(f"Command executed in container {container_id}: {command}")
            return success, stdout, ""

        except NotFound:
            logger.error(f"Container not found: {container_id}")
            return False, "", "Container not found"
        except Exception as e:
            error_msg = f"Failed to execute command in container {container_id}: {e}"
            logger.error(error_msg)
            return False, "", error_msg

    def create_tenant_network(self, network_name: str = "nlp2sql_tenant_network") -> bool:
        """
        Create a dedicated network for tenant containers.

        Args:
            network_name: Name of the network to create

        Returns:
            True if network created or already exists
        """
        try:
            # Check if network already exists
            try:
                network = self.client.networks.get(network_name)
                logger.info(f"Network already exists: {network_name}")
                return True
            except NotFound:
                pass

            # Create network
            network = self.client.networks.create(
                network_name,
                driver="bridge",
                enable_ipv6=False,
                labels={
                    "purpose": "nlp2sql-tenant-isolation",
                    "created_by": "database-cloner"
                }
            )

            logger.info(f"Network created: {network_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create network {network_name}: {e}")
            return False

    def remove_tenant_network(self, network_name: str = "nlp2sql_tenant_network") -> bool:
        """
        Remove the tenant network.

        Args:
            network_name: Name of the network to remove

        Returns:
            True if network removed successfully
        """
        try:
            network = self.client.networks.get(network_name)
            network.remove()

            logger.info(f"Network removed: {network_name}")
            return True

        except NotFound:
            logger.warning(f"Network not found: {network_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove network {network_name}: {e}")
            return False

    def create_volume(self, volume_name: str, driver: str = "local",
                     labels: Dict[str, str] = None) -> Optional[Volume]:
        """
        Create a Docker volume.

        Args:
            volume_name: Name of the volume
            driver: Volume driver
            labels: Volume labels

        Returns:
            Volume object or None if creation failed
        """
        try:
            volume = self.client.volumes.create(
                name=volume_name,
                driver=driver,
                labels=labels or {}
            )

            logger.info(f"Volume created: {volume_name}")
            return volume

        except Exception as e:
            logger.error(f"Failed to create volume {volume_name}: {e}")
            return None

    def remove_volume(self, volume_name: str, force: bool = False) -> bool:
        """
        Remove a Docker volume.

        Args:
            volume_name: Name of the volume to remove
            force: Force removal

        Returns:
            True if removed successfully
        """
        try:
            volume = self.client.volumes.get(volume_name)
            volume.remove(force=force)

            logger.info(f"Volume removed: {volume_name}")
            return True

        except NotFound:
            logger.warning(f"Volume not found: {volume_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove volume {volume_name}: {e}")
            return False

    def cleanup_tenant_resources(self, tenant_id: str) -> bool:
        """
        Cleanup all Docker resources for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            True if cleanup was successful
        """
        try:
            logger.info(f"Cleaning up Docker resources for tenant: {tenant_id}")

            cleanup_success = True

            # Remove containers
            containers = self.client.containers.list(all=True, filters={"name": f"*{tenant_id}*"})
            for container in containers:
                try:
                    if container.status == 'running':
                        container.stop(timeout=5)
                    container.remove(force=True, v=True)
                    logger.info(f"Removed container: {container.name}")
                except Exception as e:
                    logger.error(f"Failed to remove container {container.name}: {e}")
                    cleanup_success = False

            # Remove volumes
            volumes = self.client.volumes.list(filters={"label": f"tenant={tenant_id}"})
            for volume in volumes:
                try:
                    volume.remove(force=True)
                    logger.info(f"Removed volume: {volume.name}")
                except Exception as e:
                    logger.error(f"Failed to remove volume {volume.name}: {e}")
                    cleanup_success = False

            return cleanup_success

        except Exception as e:
            logger.error(f"Failed to cleanup tenant resources: {e}")
            return False

    def generate_compose_entry(self, container_config: Dict[str, Any]) -> str:
        """
        Generate docker-compose.yml entry for a tenant container.

        Args:
            container_config: Container configuration

        Returns:
            Docker compose service definition as string
        """
        try:
            service_name = container_config['name']
            image = container_config['image']
            ports = container_config.get('ports', {})
            environment = container_config.get('environment', {})
            volumes = container_config.get('volumes', {})

            # Build compose entry
            compose_entry = f"""
  {service_name}:
    image: {image}
    container_name: {service_name}
    restart: unless-stopped
"""

            # Add ports
            if ports:
                compose_entry += "    ports:\n"
                for container_port, host_port in ports.items():
                    compose_entry += f"      - \"{host_port}:{container_port.split('/')[0]}\"\n"

            # Add environment
            if environment:
                compose_entry += "    environment:\n"
                for key, value in environment.items():
                    compose_entry += f"      {key}: {value}\n"

            # Add volumes
            if volumes:
                compose_entry += "    volumes:\n"
                for host_path, container_config in volumes.items():
                    bind_path = container_config.get('bind', host_path)
                    compose_entry += f"      - {host_path}:{bind_path}\n"

            # Add network
            compose_entry += "    networks:\n      - nlp2sql_tenant_network\n"

            return compose_entry

        except Exception as e:
            logger.error(f"Failed to generate compose entry: {e}")
            return ""

    def save_tenant_compose_file(self, tenant_configs: List[Dict[str, Any]],
                                file_path: str = "docker-compose-tenants.yml") -> bool:
        """
        Save tenant container configurations to docker-compose file.

        Args:
            tenant_configs: List of tenant container configurations
            file_path: Path to save compose file

        Returns:
            True if file saved successfully
        """
        try:
            compose_content = """version: '3.8'

services:
"""

            # Add each tenant service
            for config in tenant_configs:
                compose_entry = self.generate_compose_entry(config)
                compose_content += compose_entry

            # Add networks section
            compose_content += """
networks:
  nlp2sql_tenant_network:
    external: true
"""

            # Save to file
            with open(file_path, 'w') as f:
                f.write(compose_content)

            logger.info(f"Tenant compose file saved: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save tenant compose file: {e}")
            return False

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get Docker system information.

        Returns:
            System information dictionary
        """
        try:
            info = self.client.info()
            version = self.client.version()

            return {
                'containers_running': info.get('ContainersRunning', 0),
                'containers_paused': info.get('ContainersPaused', 0),
                'containers_stopped': info.get('ContainersStopped', 0),
                'images': info.get('Images', 0),
                'docker_version': version.get('Version', 'unknown'),
                'api_version': version.get('ApiVersion', 'unknown'),
                'memory_total': info.get('MemTotal', 0),
                'cpu_count': info.get('NCPU', 0)
            }

        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {}

    # Private helper methods

    def _ensure_tenant_network(self):
        """Ensure tenant network exists."""
        self.create_tenant_network()

    def _ensure_image(self, image: str):
        """Ensure Docker image is available locally."""
        try:
            # Try to get the image locally
            self.client.images.get(image)
            logger.debug(f"Image already available: {image}")

        except NotFound:
            logger.info(f"Pulling image: {image}")
            try:
                self.client.images.pull(image)
                logger.info(f"Image pulled successfully: {image}")
            except Exception as e:
                logger.error(f"Failed to pull image {image}: {e}")
                raise

        except Exception as e:
            logger.error(f"Failed to check image {image}: {e}")
            raise