import os
from datetime import datetime
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from dotenv import load_dotenv

load_dotenv()

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/netviz"
)

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create base class for models
Base = declarative_base()

# Models
class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    message = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)

class NetworkNode(Base):
    __tablename__ = "network_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)  # router, switch, server, firewall, endpoint
    ip_address = Column(String, nullable=True)
    status = Column(String, default="unknown")  # online, offline, warning, error, unknown
    layer = Column(String, default="network")  # physical, datalink, network, transport, application
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)
    node_metadata = Column(JSON, default={})
    last_updated = Column(DateTime, default=datetime.now)
    
    # Relationships
    source_edges = relationship("NetworkEdge", foreign_keys="NetworkEdge.source_id", back_populates="source_node")
    target_edges = relationship("NetworkEdge", foreign_keys="NetworkEdge.target_id", back_populates="target_node")

class NetworkEdge(Base):
    __tablename__ = "network_edges"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("network_nodes.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("network_nodes.id"), nullable=False)
    type = Column(String, default="ethernet")  # ethernet, fiber, wireless, vpn
    bandwidth = Column(String, nullable=True)
    utilization = Column(Float, default=0.0)  # 0-100 percentage
    status = Column(String, default="unknown")  # active, inactive, error
    edge_metadata = Column(JSON, default={})
    last_updated = Column(DateTime, default=datetime.now)
    
    # Relationships
    source_node = relationship("NetworkNode", foreign_keys=[source_id], back_populates="source_edges")
    target_node = relationship("NetworkNode", foreign_keys=[target_id], back_populates="target_edges")

class GraphUpdate(Base):
    __tablename__ = "graph_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    update_type = Column(String)  # node_created, node_updated, node_deleted, edge_created, edge_updated, edge_deleted
    entity_type = Column(String)  # node, edge
    entity_id = Column(Integer)
    old_data = Column(JSON, nullable=True)
    new_data = Column(JSON, nullable=True)
    source = Column(String, default="unknown")  # api, agent, external_device
    timestamp = Column(DateTime, default=datetime.now)

# Initialize database
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Get database session
@asynccontextmanager
async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close() 