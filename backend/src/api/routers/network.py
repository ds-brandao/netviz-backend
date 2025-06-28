"""
Network API endpoints.
Handles network graph, nodes, edges, and topology management.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func

from database.database import get_db_session, NetworkNode
from src.services.graph_service import graph_service
from src.services.metrics_sync_service import metrics_sync_service
from src.models import NetworkNodeData, NetworkEdgeData, GraphUpdateRequest
from websocket_manager import connection_manager

router = APIRouter(prefix="/network", tags=["Network"])


@router.get("/graph")
async def get_network_graph():
    """Get complete network graph (nodes and edges)"""
    try:
        graph = await graph_service.get_graph()
        return {
            "nodes": list(graph["nodes"].values()),
            "edges": list(graph["edges"].values()),
            "last_updated": graph["last_updated"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes")
async def get_network_nodes():
    """Get all network nodes"""
    try:
        nodes = await graph_service.get_nodes()
        return nodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/edges")
async def get_network_edges():
    """Get all network edges"""
    try:
        edges = await graph_service.get_edges()
        return edges
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_network_stats():
    """Get network statistics"""
    try:
        stats = await graph_service.get_graph_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nodes")
async def create_network_node(node_data: NetworkNodeData):
    """Create a new network node"""
    try:
        node = await graph_service.create_node(node_data.dict(), source="api")
        return {"success": True, "node": node}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/nodes/{node_id}")
async def update_network_node(node_id: str, node_data: NetworkNodeData):
    """Update a network node"""
    try:
        node = await graph_service.update_node(node_id, node_data.dict(), source="api")
        return {"success": True, "node": node}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/nodes/{node_id}")
async def delete_network_node(node_id: str):
    """Delete a network node"""
    try:
        success = await graph_service.delete_node(node_id, source="api")
        if success:
            return {"success": True, "message": "Node deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Node not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edges")
async def create_network_edge(edge_data: NetworkEdgeData):
    """Create a new network edge"""
    try:
        edge = await graph_service.create_edge(edge_data.dict(), source="api")
        return {"success": True, "edge": edge}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/edges/{edge_id}")
async def update_network_edge(edge_id: str, edge_data: NetworkEdgeData):
    """Update a network edge"""
    try:
        edge = await graph_service.update_edge(edge_id, edge_data.dict(), source="api")
        return {"success": True, "edge": edge}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/edges/{edge_id}")
async def delete_network_edge(edge_id: str):
    """Delete a network edge"""
    try:
        success = await graph_service.delete_edge(edge_id, source="api")
        if success:
            return {"success": True, "message": "Edge deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Edge not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-update")
async def bulk_update_graph(update_request: GraphUpdateRequest):
    """Bulk update endpoint for external devices to push changes"""
    try:
        results = {"nodes": [], "edges": []}
        
        # Process node updates
        if update_request.nodes:
            for node_data in update_request.nodes:
                if "id" in node_data and node_data["id"]:
                    # Update existing node
                    node = await graph_service.update_node(
                        str(node_data["id"]), 
                        node_data, 
                        source=update_request.source
                    )
                    results["nodes"].append({"action": "updated", "node": node})
                else:
                    # Create new node
                    node = await graph_service.create_node(
                        node_data, 
                        source=update_request.source
                    )
                    results["nodes"].append({"action": "created", "node": node})
        
        # Process edge updates
        if update_request.edges:
            for edge_data in update_request.edges:
                if "id" in edge_data and edge_data["id"]:
                    # Update existing edge
                    edge = await graph_service.update_edge(
                        str(edge_data["id"]), 
                        edge_data, 
                        source=update_request.source
                    )
                    results["edges"].append({"action": "updated", "edge": edge})
                else:
                    # Create new edge
                    edge = await graph_service.create_edge(
                        edge_data, 
                        source=update_request.source
                    )
                    results["edges"].append({"action": "created", "edge": edge})
        
        return {
            "success": True,
            "message": f"Processed {len(results['nodes'])} node updates and {len(results['edges'])} edge updates",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/device-update/{device_id}")
async def device_update(device_id: str, update_data: Dict[str, Any]):
    """Simple endpoint for external devices to send updates"""
    try:
        # Find or create node for this device
        existing_node = None
        nodes = await graph_service.get_nodes()
        
        for node in nodes:
            if node.get("metadata", {}).get("device_id") == device_id:
                existing_node = node
                break
        
        # Prepare node data
        node_data = {
            "name": update_data.get("name", f"Device {device_id}"),
            "type": update_data.get("type", "endpoint"),
            "ip_address": update_data.get("ip_address"),
            "status": update_data.get("status", "online"),
            "layer": update_data.get("layer", "network"),
            "metadata": {
                "device_id": device_id,
                **update_data.get("metadata", {})
            }
        }
        
        if existing_node:
            # Update existing node
            node = await graph_service.update_node(
                existing_node["id"], 
                node_data, 
                source=f"device_{device_id}"
            )
            action = "updated"
        else:
            # Create new node
            node = await graph_service.create_node(
                node_data, 
                source=f"device_{device_id}"
            )
            action = "created"
        
        return {
            "success": True,
            "action": action,
            "node": node
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections")
async def get_connection_info():
    """Get WebSocket connection information"""
    return {
        "active_connections": connection_manager.get_connection_count(),
        "active_sessions": connection_manager.get_session_count()
    }


@router.post("/sync")
async def force_network_sync():
    """Force sync network topology from MetricBeat data"""
    try:
        await metrics_sync_service.clear_bad_data()
        await metrics_sync_service.sync_network_topology()
        return {"success": True, "message": "Network topology synced from MetricBeat data"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/clear")
async def clear_network_data():
    """Clear all bad/test network data"""
    try:
        await metrics_sync_service.clear_bad_data()
        return {"success": True, "message": "Bad/test network data cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")


@router.get("/status")
async def get_network_status():
    """Get network sync status and update information"""
    try:
        async with get_db_session() as session:
            # Get node counts by type
            result = await session.execute(
                select(NetworkNode.type, func.count(NetworkNode.id))
                .group_by(NetworkNode.type)
            )
            node_counts = {row[0]: row[1] for row in result}
            
            # Get most recent update times
            result = await session.execute(
                select(func.max(NetworkNode.last_updated))
            )
            last_node_update = result.scalar()
            
            # Get cached metrics info
            cached_metrics = metrics_sync_service.get_cached_metrics()
            
            return {
                "metrics_cache_size": cached_metrics["cache_size"],
                "last_metrics_update": cached_metrics["last_updated"],
                "last_node_update": last_node_update.isoformat() if last_node_update else None,
                "node_counts": node_counts,
                "total_nodes": sum(node_counts.values()),
                "sync_status": "active" if cached_metrics["last_updated"] else "inactive"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status fetch failed: {str(e)}")