#!/usr/bin/env python3
"""
Script to reset the database and recreate all tables with the new schema.
This will delete all existing data!
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from database.database import Base, DATABASE_URL

async def reset_database():
    """Drop all tables and recreate them"""
    print("🗑️  Resetting database...")
    print(f"📡 Database URL: {DATABASE_URL}")
    
    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        # First, drop all tables with CASCADE to handle dependencies
        print("🔥 Dropping all existing tables with CASCADE...")
        async with engine.begin() as conn:
            # Drop all tables that might exist
            drop_statements = [
                "DROP TABLE IF EXISTS graph_updates CASCADE",
                "DROP TABLE IF EXISTS network_edges CASCADE", 
                "DROP TABLE IF EXISTS network_metrics CASCADE",
                "DROP TABLE IF EXISTS network_nodes CASCADE",
                "DROP TABLE IF EXISTS chats CASCADE"
            ]
            
            for statement in drop_statements:
                try:
                    await conn.execute(text(statement))
                    print(f"✅ Executed: {statement}")
                except Exception as e:
                    print(f"⚠️  {statement} failed: {e}")
        
        # Create all tables with new schema
        print("🏗️  Creating tables with new schema...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database reset complete!")
        print("🎉 All tables recreated with the new schema.")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_database()) 