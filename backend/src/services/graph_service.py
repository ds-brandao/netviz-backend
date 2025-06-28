from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
import json

from database.database import get_db_session, NetworkNode, NetworkEdge, GraphUpdate
from websocket_manager import connection_manager

class GraphService:
    """Service for managing the network graph data structure and database synchronization"""
    
    def __init__(self):
        self._graph_cache = {
            "nodes": {},  # id -> node_data
            "edges": {},  # id -> edge_data
            "last_updated": None
        }
        self._cache_valid = False
    
    async def _invalidate_cache(self):
        """Invalidate the graph cache"""
        self._cache_valid = False
    
    async def _load_graph_from_db(self) -> Dict[str, Any]:
        """Load the complete graph from database"""
        async with get_db_session() as session:
            # Load nodes with their relationships
            nodes_result = await session.execute(
                select(NetworkNode).options(
                    selectinload(NetworkNode.source_edges),
                    selectinload(NetworkNode.target_edges)
                )
            )
            nodes = nodes_result.scalars().all()
            
            # Load edges
            edges_result = await session.execute(select(NetworkEdge))
            edges = edges_result.scalars().all()
            
            # Convert to graph format
            graph_nodes = {}
            graph_edges = {}
            
            for node in nodes:
                # Filter out None/empty values from metadata
                filtered_metadata = {k: v for k, v in (node.node_metadata or {}).items() if v is not None and v != ""}
                
                graph_nodes[str(node.id)] = {
                    "id": str(node.id),
                    "name": node.name,
                    "type": node.type,
                    "ip_address": node.ip_address,
                    "status": node.status,
                    "layer": node.layer,
                    "position": {"x": node.position_x, "y": node.position_y},
                    "metadata": filtered_metadata,
                    "last_updated": node.last_updated.isoformat() if node.last_updated else None
                }
            
            for edge in edges:
                # Filter out None/empty values from metadata
                filtered_metadata = {k: v for k, v in (edge.edge_metadata or {}).items() if v is not None and v != ""}
                
                graph_edges[str(edge.id)] = {
                    "id": str(edge.id),
                    "source": str(edge.source_id),
                    "target": str(edge.target_id),
                    "type": edge.type,
                    "bandwidth": edge.bandwidth,
                    "utilization": edge.utilization,
                    "status": edge.status,
                    "metadata": filtered_metadata,
                    "last_updated": edge.last_updated.isoformat() if edge.last_updated else None
                }
            
            return {
                "nodes": graph_nodes,
                "edges": graph_edges,
                "last_updated": datetime.now().isoformat()
            }
    
    async def get_graph(self, force_reload: bool = False) -> Dict[str, Any]:
        """Get the current graph state"""
        if not self._cache_valid or force_reload:
            self._graph_cache = await self._load_graph_from_db()
            self._cache_valid = True
        
        return self._graph_cache
    
    async def get_nodes(self) -> List[Dict[str, Any]]:
        """Get all nodes"""
        graph = await self.get_graph()
        return list(graph["nodes"].values())
    
    async def get_edges(self) -> List[Dict[str, Any]]:
        """Get all edges"""
        graph = await self.get_graph()
        return list(graph["edges"].values())
    
    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific node"""
        graph = await self.get_graph()
        return graph["nodes"].get(node_id)
    
    async def get_edge(self, edge_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific edge"""
        graph = await self.get_graph()
        return graph["edges"].get(edge_id)
    
    async def create_node(self, node_data: Dict[str, Any], source: str = "api") -> Dict[str, Any]:
        """Create a new node"""
        async with get_db_session() as session:
            # Extract position if provided
            position = node_data.get("position", {"x": 0.0, "y": 0.0})
            
            # Filter metadata to remove None/empty values
            metadata = {k: v for k, v in (node_data.get("metadata", {})).items() if v is not None and v != ""}
            
            node = NetworkNode(
                name=node_data["name"],
                type=node_data["type"],
                ip_address=node_data.get("ip_address"),
                status=node_data.get("status", "unknown"),
                layer=node_data.get("layer", "network"),
                position_x=position["x"],
                position_y=position["y"],
                node_metadata=metadata,
                last_updated=datetime.now()
            )
            
            session.add(node)
            await session.flush()  # Get the ID
            
            # Log the update
            update = GraphUpdate(
                update_type="node_created",
                entity_type="node",
                entity_id=node.id,
                old_data=None,
                new_data=node_data,
                source=source,
                timestamp=datetime.now()
            )
            session.add(update)
            await session.commit()
            
            # Invalidate cache and get updated node data
            await self._invalidate_cache()
            node_result = await self.get_node(str(node.id))
            
            # Broadcast update
            await connection_manager.broadcast_graph_update(
                "created", "node", node_result, source
            )
            
            return node_result
    
    async def update_node(self, node_id: str, node_data: Dict[str, Any], source: str = "api") -> Dict[str, Any]:
        """Update an existing node"""
        async with get_db_session() as session:
            result = await session.execute(
                select(NetworkNode).where(NetworkNode.id == int(node_id))
            )
            node = result.scalar_one_or_none()
            
            if not node:
                raise ValueError(f"Node {node_id} not found")
            
            # Store old data for logging
            old_data = {
                "name": node.name,
                "type": node.type,
                "ip_address": node.ip_address,
                "status": node.status,
                "layer": node.layer,
                "position": {"x": node.position_x, "y": node.position_y},
                "metadata": node.node_metadata
            }
            
            # Update fields
            if "name" in node_data:
                node.name = node_data["name"]
            if "type" in node_data:
                node.type = node_data["type"]
            if "ip_address" in node_data:
                node.ip_address = node_data["ip_address"]
            if "status" in node_data:
                node.status = node_data["status"]
            if "layer" in node_data:
                node.layer = node_data["layer"]
            if "position" in node_data:
                node.position_x = node_data["position"]["x"]
                node.position_y = node_data["position"]["y"]
            if "metadata" in node_data:
                # Filter metadata to remove None/empty values
                filtered_metadata = {k: v for k, v in node_data["metadata"].items() if v is not None and v != ""}
                node.node_metadata = filtered_metadata
            
            node.last_updated = datetime.now()
            
            # Log the update
            update = GraphUpdate(
                update_type="node_updated",
                entity_type="node",
                entity_id=node.id,
                old_data=old_data,
                new_data=node_data,
                source=source,
                timestamp=datetime.now()
            )
            session.add(update)
            await session.commit()
            
            # Invalidate cache and get updated node data
            await self._invalidate_cache()
            node_result = await self.get_node(str(node.id))
            
            # Broadcast update
            await connection_manager.broadcast_graph_update(
                "updated", "node", node_result, source
            )
            
            return node_result
    
    async def delete_node(self, node_id: str, source: str = "api") -> bool:
        """Delete a node and its associated edges"""
        async with get_db_session() as session:
            # Get node data before deletion
            node_result = await self.get_node(node_id)
            if not node_result:
                return False
            
            # Delete associated edges first
            await session.execute(
                delete(NetworkEdge).where(
                    (NetworkEdge.source_id == int(node_id)) |
                    (NetworkEdge.target_id == int(node_id))
                )
            )
            
            # Delete the node
            await session.execute(
                delete(NetworkNode).where(NetworkNode.id == int(node_id))
            )
            
            # Log the update
            update = GraphUpdate(
                update_type="node_deleted",
                entity_type="node",
                entity_id=int(node_id),
                old_data=node_result,
                new_data=None,
                source=source,
                timestamp=datetime.now()
            )
            session.add(update)
            await session.commit()
            
            # Invalidate cache
            await self._invalidate_cache()
            
            # Broadcast update
            await connection_manager.broadcast_graph_update(
                "deleted", "node", node_result, source
            )
            
            return True
    
    async def create_edge(self, edge_data: Dict[str, Any], source: str = "api") -> Dict[str, Any]:
        """Create a new edge"""
        async with get_db_session() as session:
            # Filter metadata to remove None/empty values
            metadata = {k: v for k, v in (edge_data.get("metadata", {})).items() if v is not None and v != ""}
            
            edge = NetworkEdge(
                source_id=int(edge_data["source"]),
                target_id=int(edge_data["target"]),
                type=edge_data.get("type", "ethernet"),
                bandwidth=edge_data.get("bandwidth"),
                utilization=edge_data.get("utilization", 0.0),
                status=edge_data.get("status", "unknown"),
                edge_metadata=metadata,
                last_updated=datetime.now()
            )
            
            session.add(edge)
            await session.flush()  # Get the ID
            
            # Log the update
            update = GraphUpdate(
                update_type="edge_created",
                entity_type="edge",
                entity_id=edge.id,
                old_data=None,
                new_data=edge_data,
                source=source,
                timestamp=datetime.now()
            )
            session.add(update)
            await session.commit()
            
            # Invalidate cache and get updated edge data
            await self._invalidate_cache()
            edge_result = await self.get_edge(str(edge.id))
            
            # Broadcast update
            await connection_manager.broadcast_graph_update(
                "created", "edge", edge_result, source
            )
            
            return edge_result
    
    async def update_edge(self, edge_id: str, edge_data: Dict[str, Any], source: str = "api") -> Dict[str, Any]:
        """Update an existing edge"""
        async with get_db_session() as session:
            result = await session.execute(
                select(NetworkEdge).where(NetworkEdge.id == int(edge_id))
            )
            edge = result.scalar_one_or_none()
            
            if not edge:
                raise ValueError(f"Edge {edge_id} not found")
            
            # Store old data for logging
            old_data = {
                "source": str(edge.source_id),
                "target": str(edge.target_id),
                "type": edge.type,
                "bandwidth": edge.bandwidth,
                "utilization": edge.utilization,
                "status": edge.status,
                "metadata": edge.edge_metadata
            }
            
            # Update fields
            if "source" in edge_data:
                edge.source_id = int(edge_data["source"])
            if "target" in edge_data:
                edge.target_id = int(edge_data["target"])
            if "type" in edge_data:
                edge.type = edge_data["type"]
            if "bandwidth" in edge_data:
                edge.bandwidth = edge_data["bandwidth"]
            if "utilization" in edge_data:
                edge.utilization = edge_data["utilization"]
            if "status" in edge_data:
                edge.status = edge_data["status"]
            if "metadata" in edge_data:
                # Filter metadata to remove None/empty values
                filtered_metadata = {k: v for k, v in edge_data["metadata"].items() if v is not None and v != ""}
                edge.edge_metadata = filtered_metadata
            
            edge.last_updated = datetime.now()
            
            # Log the update
            update = GraphUpdate(
                update_type="edge_updated",
                entity_type="edge",
                entity_id=edge.id,
                old_data=old_data,
                new_data=edge_data,
                source=source,
                timestamp=datetime.now()
            )
            session.add(update)
            await session.commit()
            
            # Invalidate cache and get updated edge data
            await self._invalidate_cache()
            edge_result = await self.get_edge(str(edge.id))
            
            # Broadcast update
            await connection_manager.broadcast_graph_update(
                "updated", "edge", edge_result, source
            )
            
            return edge_result
    
    async def delete_edge(self, edge_id: str, source: str = "api") -> bool:
        """Delete an edge"""
        async with get_db_session() as session:
            # Get edge data before deletion
            edge_result = await self.get_edge(edge_id)
            if not edge_result:
                return False
            
            # Delete the edge
            await session.execute(
                delete(NetworkEdge).where(NetworkEdge.id == int(edge_id))
            )
            
            # Log the update
            update = GraphUpdate(
                update_type="edge_deleted",
                entity_type="edge",
                entity_id=int(edge_id),
                old_data=edge_result,
                new_data=None,
                source=source,
                timestamp=datetime.now()
            )
            session.add(update)
            await session.commit()
            
            # Invalidate cache
            await self._invalidate_cache()
            
            # Broadcast update
            await connection_manager.broadcast_graph_update(
                "deleted", "edge", edge_result, source
            )
            
            return True
    
    async def get_graph_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        graph = await self.get_graph()
        nodes = graph["nodes"]
        edges = graph["edges"]
        
        # Count nodes by status
        node_status_counts = {}
        for node in nodes.values():
            status = node["status"]
            node_status_counts[status] = node_status_counts.get(status, 0) + 1
        
        # Count edges by status
        edge_status_counts = {}
        for edge in edges.values():
            status = edge["status"]
            edge_status_counts[status] = edge_status_counts.get(status, 0) + 1
        
        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_status_counts": node_status_counts,
            "edge_status_counts": edge_status_counts,
            "last_updated": graph["last_updated"]
        }

# Global graph service instance
graph_service = GraphService() 