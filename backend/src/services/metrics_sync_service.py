"""
Metrics synchronization service for syncing network topology based on MetricBeat data.
"""

from typing import Dict, Set, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import get_db_session, NetworkNode, NetworkEdge
from src.config import settings
from .opensearch_service import opensearch_service


class MetricsSyncService:
    """Service for syncing network topology from metrics data"""
    
    def __init__(self):
        self.metrics_cache: Dict[str, Any] = {}
        self.last_metrics_update: Optional[datetime] = None
    
    async def sync_network_topology(self) -> None:
        """Sync network topology based on MetricBeat data"""
        try:
            # Get fresh metrics
            metrics = await opensearch_service.fetch_metrics()
            
            if not metrics:
                print("No metrics available for topology sync")
                return
                
            async with get_db_session() as session:
                # Get existing nodes
                result = await session.execute(select(NetworkNode))
                existing_nodes = {node.name: node for node in result.scalars().all()}
                
                current_time = datetime.now()
                updated_nodes = set()
                
                # Process each host from metrics
                for host_name, host_data in metrics.items():
                    # Create or update host node
                    host_node_name = f"host-{host_name}"
                    await self._process_host_node(
                        session, existing_nodes, host_node_name, 
                        host_data, current_time, updated_nodes
                    )
                    
                    # Process containers for this host
                    containers = host_data.get("containers", [])
                    for container in containers:
                        await self._process_container_node(
                            session, existing_nodes, container, 
                            host_name, current_time, updated_nodes
                        )
                
                # Clean up stale nodes
                await self._cleanup_stale_nodes(
                    session, existing_nodes, updated_nodes, current_time
                )
                
                # Create network topology edges based on demo-infra structure
                await self._create_demo_network_edges(session)
                
                await session.commit()
                print(f"Synced network topology: {len(updated_nodes)} nodes updated")
                
            # Update cache
            self.metrics_cache = metrics
            self.last_metrics_update = datetime.now()
                
        except Exception as e:
            print(f"Error syncing network topology: {e}")
    
    async def _process_host_node(
        self, 
        session: AsyncSession,
        existing_nodes: Dict[str, NetworkNode],
        host_node_name: str,
        host_data: Dict[str, Any],
        current_time: datetime,
        updated_nodes: Set[str]
    ) -> None:
        """Process and update/create host node"""
        if host_node_name in existing_nodes:
            host_node = existing_nodes[host_node_name]
            host_node.last_updated = current_time
            host_node.status = "online"
            host_node.node_metadata.update({
                "cpu_usage": host_data.get("cpu_usage"),
                "memory_usage": host_data.get("memory_usage"),
                "memory_total": host_data.get("memory_total"),
                "memory_used": host_data.get("memory_used"),
                "disk_usage": host_data.get("disk_usage"),
                "load_average": host_data.get("load_average"),
                "uptime": host_data.get("uptime"),
                "metric_source": "metricbeat"
            })
        else:
            host_node = NetworkNode(
                name=host_node_name,
                type="host",
                ip_address=None,
                status="online",
                layer="infrastructure",
                position_x=0.0,
                position_y=0.0,
                node_metadata={
                    "cpu_usage": host_data.get("cpu_usage"),
                    "memory_usage": host_data.get("memory_usage"),
                    "memory_total": host_data.get("memory_total"),
                    "memory_used": host_data.get("memory_used"),
                    "disk_usage": host_data.get("disk_usage"),
                    "load_average": host_data.get("load_average"),
                    "uptime": host_data.get("uptime"),
                    "metric_source": "metricbeat"
                },
                last_updated=current_time
            )
            session.add(host_node)
            
        updated_nodes.add(host_node_name)
    
    async def _process_container_node(
        self,
        session: AsyncSession,
        existing_nodes: Dict[str, NetworkNode],
        container: Dict[str, Any],
        host_name: str,
        current_time: datetime,
        updated_nodes: Set[str]
    ) -> None:
        """Process and update/create container node"""
        container_name = container.get("name")
        if not container_name:
            return
            
        # Map container names to network device types
        device_type = settings.DEVICE_TYPE_MAPPINGS.get(container_name, "container")
        
        # Determine IP based on container name
        ip_address = settings.DEVICE_IP_MAPPINGS.get(container_name)
        
        if container_name in existing_nodes:
            container_node = existing_nodes[container_name]
            container_node.last_updated = current_time
            container_node.status = "online" if "Up" in container.get("status", "") else "offline"
            container_node.type = device_type
            container_node.ip_address = ip_address
            container_node.node_metadata.update({
                "container_id": container.get("id"),
                "container_status": container.get("status"),
                "cpu_usage": container.get("cpu_usage"),
                "memory_usage": container.get("memory_usage"),
                "host": host_name,
                "metric_source": "metricbeat"
            })
        else:
            container_node = NetworkNode(
                name=container_name,
                type=device_type,
                ip_address=ip_address,
                status="online" if "Up" in container.get("status", "") else "offline",
                layer="network",
                position_x=0.0,
                position_y=0.0,
                node_metadata={
                    "container_id": container.get("id"),
                    "container_status": container.get("status"),
                    "cpu_usage": container.get("cpu_usage"),
                    "memory_usage": container.get("memory_usage"),
                    "host": host_name,
                    "metric_source": "metricbeat"
                },
                last_updated=current_time
            )
            session.add(container_node)
            
        updated_nodes.add(container_name)
    
    async def _cleanup_stale_nodes(
        self,
        session: AsyncSession,
        existing_nodes: Dict[str, NetworkNode],
        updated_nodes: Set[str],
        current_time: datetime
    ) -> None:
        """Clean up stale nodes (only ones without MetricBeat data and older than 30 minutes)"""
        stale_threshold = current_time - timedelta(minutes=30)
        for node_name, node in existing_nodes.items():
            if (node_name not in updated_nodes and 
                node.last_updated < stale_threshold and
                node.node_metadata.get("metric_source") != "metricbeat"):
                print(f"Removing stale node: {node_name}")
                await session.delete(node)
    
    async def _create_demo_network_edges(self, session: AsyncSession) -> None:
        """Create edges representing the demo-infra network topology"""
        # Get all nodes by name
        result = await session.execute(select(NetworkNode))
        nodes_by_name = {node.name: node for node in result.scalars().all()}
        
        # Get existing edges
        edge_result = await session.execute(select(NetworkEdge))
        existing_edges = {(edge.source_node.name, edge.target_node.name): edge 
                         for edge in edge_result.scalars().all()}
        
        current_time = datetime.now()
        
        for source_name, target_name, connection_type in settings.DEMO_NETWORK_TOPOLOGY:
            if source_name in nodes_by_name and target_name in nodes_by_name:
                source_node = nodes_by_name[source_name]
                target_node = nodes_by_name[target_name]
                
                # Check if edge already exists (in either direction)
                edge_key = (source_name, target_name)
                reverse_edge_key = (target_name, source_name)
                
                if edge_key not in existing_edges and reverse_edge_key not in existing_edges:
                    # Determine subnet based on connection
                    subnet_info = settings.SUBNET_INFO.get(edge_key, "1Gbps")
                    
                    # Create new edge
                    new_edge = NetworkEdge(
                        source_id=source_node.id,
                        target_id=target_node.id,
                        type=connection_type,
                        bandwidth=subnet_info,
                        utilization=0.0,
                        status="active",
                        edge_metadata={
                            "auto_created": True, 
                            "topology": "demo-infra",
                            "subnet": subnet_info.split(" (")[0] if "(" in subnet_info else "N/A"
                        },
                        last_updated=current_time
                    )
                    session.add(new_edge)
                elif edge_key in existing_edges:
                    # Update existing edge
                    edge = existing_edges[edge_key]
                    edge.last_updated = current_time
                    edge.status = "active"
                    # Update subnet info if not already set
                    if "subnet" not in edge.edge_metadata:
                        subnet_info = settings.SUBNET_INFO.get(edge_key, "1Gbps")
                        edge.bandwidth = subnet_info
                        edge.edge_metadata["subnet"] = subnet_info.split(" (")[0] if "(" in subnet_info else "N/A"
    
    async def clear_bad_data(self) -> None:
        """Clear test devices and invalid string entries"""
        try:
            async with get_db_session() as session:
                # Delete nodes with invalid data
                result = await session.execute(select(NetworkNode))
                nodes_to_delete = []
                
                for node in result.scalars().all():
                    # Mark for deletion if it's test data or invalid
                    node_name_lower = node.name.lower() if node.name else ""
                    
                    # Check for test device patterns
                    test_prefixes = ["retrieved ", "concurrent ", "test ", "bulk ", "status test", "metadata test"]
                    is_test_device = any(node_name_lower.startswith(prefix) for prefix in test_prefixes)
                    
                    if (node.name in ["string", "Device test-device-001"] or 
                        node.type == "string" or 
                        node.ip_address == "string" or
                        "test-device" in node.name or
                        is_test_device):
                        nodes_to_delete.append(node.id)
                
                if nodes_to_delete:
                    # Delete associated edges first
                    await session.execute(
                        delete(NetworkEdge).where(
                            (NetworkEdge.source_id.in_(nodes_to_delete)) |
                            (NetworkEdge.target_id.in_(nodes_to_delete))
                        )
                    )
                    
                    # Delete the nodes
                    await session.execute(
                        delete(NetworkNode).where(NetworkNode.id.in_(nodes_to_delete))
                    )
                    
                    await session.commit()
                    print(f"Cleared {len(nodes_to_delete)} bad/test nodes and their edges")
                else:
                    print("No bad data found to clear")
                    
        except Exception as e:
            print(f"Error clearing bad data: {e}")
    
    def get_cached_metrics(self) -> Dict[str, Any]:
        """Get cached metrics"""
        return {
            "metrics": self.metrics_cache,
            "last_updated": self.last_metrics_update.isoformat() if self.last_metrics_update else None,
            "cache_size": len(self.metrics_cache)
        }
    
    def should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed"""
        if not self.metrics_cache or not self.last_metrics_update:
            return True
        return (datetime.now() - self.last_metrics_update).seconds > settings.METRICS_CACHE_TTL_SECONDS


# Create a global instance
metrics_sync_service = MetricsSyncService()