"""
Docker Service - Manages Docker containers via Docker API
"""
import docker
from docker.errors import NotFound, APIError, ImageNotFound
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DockerService:
    """Service for managing Docker containers"""
    
    def __init__(self):
        """Initialize Docker client"""
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Docker client connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            raise
    
    def list_containers(self, all_containers: bool = True) -> List[Dict]:
        """List all containers with their details"""
        containers = []
        try:
            for container in self.client.containers.list(all=all_containers):
                containers.append({
                    "id": container.short_id,
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else "unknown",
                    "status": container.status,
                    "created": container.attrs.get("Created", ""),
                    "ports": self._format_ports(container.ports)
                })
        except APIError as e:
            logger.error(f"Error listing containers: {e}")
            raise
        return containers
    
    def get_container_status(self, container_name: str) -> Dict:
        """Get detailed status of a specific container"""
        try:
            container = self.client.containers.get(container_name)
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_percent = self._calculate_cpu_percent(stats)
            
            # Calculate memory usage
            memory_usage = self._calculate_memory_usage(stats)
            
            return {
                "name": container.name,
                "id": container.short_id,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "created": container.attrs.get("Created", ""),
                "started_at": container.attrs.get("State", {}).get("StartedAt", ""),
                "cpu_percent": cpu_percent,
                "memory_usage": memory_usage,
                "ports": self._format_ports(container.ports),
                "health": container.attrs.get("State", {}).get("Health", {}).get("Status", "N/A")
            }
        except NotFound:
            logger.warning(f"Container {container_name} not found")
            return {"error": f"Container '{container_name}' not found"}
        except APIError as e:
            logger.error(f"Error getting container status: {e}")
            raise
    
    def get_container_logs(self, container_name: str, lines: int = 50) -> str:
        """Get container logs"""
        try:
            container = self.client.containers.get(container_name)
            logs = container.logs(tail=lines, timestamps=True).decode('utf-8')
            return logs if logs else "No logs available"
        except NotFound:
            return f"Container '{container_name}' not found"
        except APIError as e:
            logger.error(f"Error getting logs: {e}")
            return f"Error retrieving logs: {str(e)}"
    
    def deploy_container(self, image: str, name: str, ports: Optional[Dict] = None, 
                        env_vars: Optional[Dict] = None, restart_policy: str = "unless-stopped") -> Tuple[bool, str]:
        """Deploy a new container from an image"""
        try:
            # Check if container with same name exists
            try:
                existing = self.client.containers.get(name)
                existing.stop()
                existing.remove()
                logger.info(f"Removed existing container: {name}")
            except NotFound:
                pass
            
            # Pull the image first
            logger.info(f"Pulling image: {image}")
            self.client.images.pull(image)
            
            # Create and start container
            container = self.client.containers.run(
                image=image,
                name=name,
                ports=ports or {},
                environment=env_vars or {},
                detach=True,
                restart_policy={"Name": restart_policy}
            )
            
            logger.info(f"Container {name} deployed successfully")
            return True, f"✅ Container '{name}' deployed successfully!\nID: {container.short_id}\nImage: {image}"
            
        except ImageNotFound:
            return False, f"❌ Image '{image}' not found"
        except APIError as e:
            logger.error(f"Deployment failed: {e}")
            return False, f"❌ Deployment failed: {str(e)}"
    
    def rollback_container(self, container_name: str, previous_image: str) -> Tuple[bool, str]:
        """Rollback container to a previous image version"""
        try:
            container = self.client.containers.get(container_name)
            
            # Get current container config
            ports = container.ports
            env_vars = container.attrs.get("Config", {}).get("Env", [])
            
            # Convert env list to dict
            env_dict = {}
            for env in env_vars:
                if "=" in env:
                    key, value = env.split("=", 1)
                    env_dict[key] = value
            
            # Stop and remove current container
            container.stop()
            container.remove()
            
            # Deploy with previous image
            success, message = self.deploy_container(
                image=previous_image,
                name=container_name,
                ports=ports,
                env_vars=env_dict
            )
            
            if success:
                return True, f"🔄 Rollback successful!\nContainer '{container_name}' now running image: {previous_image}"
            return False, message
            
        except NotFound:
            return False, f"❌ Container '{container_name}' not found"
        except APIError as e:
            logger.error(f"Rollback failed: {e}")
            return False, f"❌ Rollback failed: {str(e)}"
    
    def start_container(self, container_name: str) -> Tuple[bool, str]:
        """Start a stopped container"""
        try:
            container = self.client.containers.get(container_name)
            container.start()
            return True, f"▶️ Container '{container_name}' started successfully"
        except NotFound:
            return False, f"❌ Container '{container_name}' not found"
        except APIError as e:
            return False, f"❌ Failed to start container: {str(e)}"
    
    def stop_container(self, container_name: str) -> Tuple[bool, str]:
        """Stop a running container"""
        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=30)
            return True, f"⏹️ Container '{container_name}' stopped successfully"
        except NotFound:
            return False, f"❌ Container '{container_name}' not found"
        except APIError as e:
            return False, f"❌ Failed to stop container: {str(e)}"
    
    def restart_container(self, container_name: str) -> Tuple[bool, str]:
        """Restart a container"""
        try:
            container = self.client.containers.get(container_name)
            container.restart(timeout=30)
            return True, f"🔄 Container '{container_name}' restarted successfully"
        except NotFound:
            return False, f"❌ Container '{container_name}' not found"
        except APIError as e:
            return False, f"❌ Failed to restart container: {str(e)}"
    
    def get_container_stats(self, container_name: str) -> Dict:
        """Get real-time stats for a container"""
        try:
            container = self.client.containers.get(container_name)
            stats = container.stats(stream=False)
            
            return {
                "name": container_name,
                "cpu_percent": self._calculate_cpu_percent(stats),
                "memory": self._calculate_memory_usage(stats),
                "network_io": self._calculate_network_io(stats),
                "block_io": self._calculate_block_io(stats)
            }
        except NotFound:
            return {"error": f"Container '{container_name}' not found"}
        except APIError as e:
            return {"error": str(e)}
    
    def health_check_all(self) -> List[Dict]:
        """Perform health check on all running containers"""
        results = []
        for container in self.client.containers.list():
            health = container.attrs.get("State", {}).get("Health", {})
            results.append({
                "name": container.name,
                "status": container.status,
                "health": health.get("Status", "no healthcheck"),
                "image": container.image.tags[0] if container.image.tags else "unknown"
            })
        return results
    
    def _format_ports(self, ports: Dict) -> str:
        """Format port mappings for display"""
        if not ports:
            return "None"
        formatted = []
        for container_port, host_bindings in ports.items():
            if host_bindings:
                for binding in host_bindings:
                    formatted.append(f"{binding['HostPort']}->{container_port}")
            else:
                formatted.append(container_port)
        return ", ".join(formatted)
    
    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU usage percentage"""
        try:
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                       stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                          stats["precpu_stats"]["system_cpu_usage"]
            num_cpus = stats["cpu_stats"]["online_cpus"]
            
            if system_delta > 0 and cpu_delta > 0:
                return round((cpu_delta / system_delta) * num_cpus * 100, 2)
        except (KeyError, TypeError, ZeroDivisionError):
            pass
        return 0.0
    
    def _calculate_memory_usage(self, stats: Dict) -> Dict:
        """Calculate memory usage"""
        try:
            usage = stats["memory_stats"]["usage"]
            limit = stats["memory_stats"]["limit"]
            percent = round((usage / limit) * 100, 2) if limit > 0 else 0
            return {
                "used": self._format_bytes(usage),
                "limit": self._format_bytes(limit),
                "percent": percent
            }
        except (KeyError, TypeError):
            return {"used": "N/A", "limit": "N/A", "percent": 0}
    
    def _calculate_network_io(self, stats: Dict) -> Dict:
        """Calculate network I/O"""
        try:
            networks = stats.get("networks", {})
            rx_bytes = sum(net.get("rx_bytes", 0) for net in networks.values())
            tx_bytes = sum(net.get("tx_bytes", 0) for net in networks.values())
            return {
                "rx": self._format_bytes(rx_bytes),
                "tx": self._format_bytes(tx_bytes)
            }
        except (KeyError, TypeError):
            return {"rx": "N/A", "tx": "N/A"}
    
    def _calculate_block_io(self, stats: Dict) -> Dict:
        """Calculate block I/O"""
        try:
            blkio = stats.get("blkio_stats", {}).get("io_service_bytes_recursive", [])
            read_bytes = sum(item.get("value", 0) for item in blkio if item.get("op") == "Read")
            write_bytes = sum(item.get("value", 0) for item in blkio if item.get("op") == "Write")
            return {
                "read": self._format_bytes(read_bytes),
                "write": self._format_bytes(write_bytes)
            }
        except (KeyError, TypeError):
            return {"read": "N/A", "write": "N/A"}
    
    @staticmethod
    def _format_bytes(bytes_val: int) -> str:
        """Format bytes to human readable string"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.2f} PB"
