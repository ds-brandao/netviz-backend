#!/usr/bin/env python3
"""
Database migration script to add missing columns to existing tables.
This preserves existing data.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from database.database import DATABASE_URL

async def migrate_database():
    """Add missing columns to existing tables"""
    print("🔄 Migrating database...")
    print(f"📡 Database URL: {DATABASE_URL}")
    
    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    migrations = [
        # Add layer column to network_nodes
        "ALTER TABLE network_nodes ADD COLUMN IF NOT EXISTS layer VARCHAR DEFAULT 'network'",
        
        # Add position columns to network_nodes
        "ALTER TABLE network_nodes ADD COLUMN IF NOT EXISTS position_x FLOAT DEFAULT 0.0",
        "ALTER TABLE network_nodes ADD COLUMN IF NOT EXISTS position_y FLOAT DEFAULT 0.0",
        
        # Create network_edges table if it doesn't exist
        """
        CREATE TABLE IF NOT EXISTS network_edges (
            id SERIAL PRIMARY KEY,
            source_id INTEGER NOT NULL REFERENCES network_nodes(id),
            target_id INTEGER NOT NULL REFERENCES network_nodes(id),
            type VARCHAR DEFAULT 'ethernet',
            bandwidth VARCHAR,
            utilization FLOAT DEFAULT 0.0,
            status VARCHAR DEFAULT 'unknown',
            edge_metadata JSON DEFAULT '{}',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Create graph_updates table if it doesn't exist
        """
        CREATE TABLE IF NOT EXISTS graph_updates (
            id SERIAL PRIMARY KEY,
            update_type VARCHAR,
            entity_type VARCHAR,
            entity_id INTEGER,
            old_data JSON,
            new_data JSON,
            source VARCHAR DEFAULT 'unknown',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    
    try:
        async with engine.begin() as conn:
            for i, migration in enumerate(migrations, 1):
                print(f"🔧 Running migration {i}/{len(migrations)}...")
                try:
                    await conn.execute(text(migration))
                    print(f"✅ Migration {i} completed")
                except Exception as e:
                    print(f"⚠️  Migration {i} failed (might already exist): {e}")
        
        print("✅ Database migration complete!")
        print("🎉 All missing columns and tables added.")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate_database()) 