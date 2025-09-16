"""
PostgreSQL Connection Pool Configuration for SaaS Control Deck
Environment-specific connection pool settings optimized for different workloads
"""

import asyncio
import asyncpg
from typing import Dict, Any, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class PoolConfig:
    """Connection pool configuration for different environments"""
    min_size: int
    max_size: int
    command_timeout: int
    query_timeout: int
    server_settings: Dict[str, str]
    pool_recycle: int  # Seconds before recreating connections
    retry_attempts: int
    retry_delay: float

# Environment-specific connection pool configurations
POOL_CONFIGS = {
    "development": PoolConfig(
        min_size=2,
        max_size=8,
        command_timeout=30,
        query_timeout=60,
        server_settings={
            'application_name': 'saascontrol_dev',
            'statement_timeout': '60s',
            'lock_timeout': '30s',
            'jit': 'off',  # Disable JIT for dev (faster small queries)
            'work_mem': '16MB',
            'temp_buffers': '32MB'
        },
        pool_recycle=3600,  # 1 hour
        retry_attempts=3,
        retry_delay=1.0
    ),
    
    "staging": PoolConfig(
        min_size=5,
        max_size=15,
        command_timeout=45,
        query_timeout=120,
        server_settings={
            'application_name': 'saascontrol_stage',
            'statement_timeout': '120s',
            'lock_timeout': '45s',
            'jit': 'on',
            'jit_above_cost': '100000',
            'work_mem': '24MB',
            'temp_buffers': '48MB',
            'maintenance_work_mem': '128MB'
        },
        pool_recycle=1800,  # 30 minutes
        retry_attempts=5,
        retry_delay=2.0
    ),
    
    "production": PoolConfig(
        min_size=10,
        max_size=25,
        command_timeout=60,
        query_timeout=300,
        server_settings={
            'application_name': 'saascontrol_prod',
            'statement_timeout': '300s',
            'lock_timeout': '60s',
            'jit': 'on',
            'jit_above_cost': '50000',
            'work_mem': '32MB',
            'temp_buffers': '64MB',
            'maintenance_work_mem': '256MB',
            'shared_preload_libraries': 'pg_stat_statements',
            'track_activities': 'on',
            'track_counts': 'on'
        },
        pool_recycle=1200,  # 20 minutes
        retry_attempts=10,
        retry_delay=5.0
    )
}

# Service-specific pool size multipliers
SERVICE_MULTIPLIERS = {
    "api_gateway": 1.2,  # Higher load from frontend requests
    "data_service": 1.5,  # Database-intensive operations
    "ai_service": 0.8     # Longer-running but fewer concurrent operations
}

class OptimizedDatabase:
    """Enhanced database connection manager with environment-specific optimization"""
    
    _pools: Dict[str, asyncpg.Pool] = {}
    _environment: Optional[str] = None
    
    @classmethod
    async def initialize_pools(cls, environment: str, database_configs: Dict[str, str]):
        """Initialize connection pools for all databases in the environment"""
        cls._environment = environment
        pool_config = POOL_CONFIGS.get(environment, POOL_CONFIGS["development"])
        
        for service, db_url in database_configs.items():
            # Apply service-specific multipliers
            multiplier = SERVICE_MULTIPLIERS.get(service, 1.0)
            adjusted_max_size = int(pool_config.max_size * multiplier)
            adjusted_min_size = max(1, int(pool_config.min_size * multiplier))
            
            try:
                pool = await asyncpg.create_pool(
                    db_url,
                    min_size=adjusted_min_size,
                    max_size=adjusted_max_size,
                    command_timeout=pool_config.command_timeout,
                    server_settings=pool_config.server_settings,
                    setup=cls._setup_connection
                )
                
                cls._pools[service] = pool
                
                logger.info(
                    "Database pool initialized",
                    service=service,
                    environment=environment,
                    min_size=adjusted_min_size,
                    max_size=adjusted_max_size
                )
                
            except Exception as e:
                logger.error(
                    "Failed to initialize database pool",
                    service=service,
                    error=str(e),
                    exc_info=True
                )
                raise
    
    @classmethod
    async def _setup_connection(cls, connection: asyncpg.Connection):
        """Setup function called for each new connection"""
        # Set connection-specific optimizations
        await connection.execute("SET timezone = 'UTC'")
        await connection.execute("SET standard_conforming_strings = on")
        
        # Environment-specific connection setup
        if cls._environment == "production":
            # Production-specific settings
            await connection.execute("SET log_statement_stats = off")
            await connection.execute("SET log_parser_stats = off")
            await connection.execute("SET log_planner_stats = off")
            await connection.execute("SET log_executor_stats = off")
        elif cls._environment == "development":
            # Development-specific settings for debugging
            await connection.execute("SET log_min_duration_statement = '1s'")
            await connection.execute("SET auto_explain.log_min_duration = '2s'")
    
    @classmethod
    def get_pool(cls, service: str) -> asyncpg.Pool:
        """Get connection pool for specific service"""
        if service not in cls._pools:
            raise ValueError(f"No pool found for service: {service}")
        return cls._pools[service]
    
    @classmethod
    async def close_all_pools(cls):
        """Close all connection pools"""
        for service, pool in cls._pools.items():
            if pool:
                await pool.close()
                logger.info("Database pool closed", service=service)
        cls._pools.clear()
    
    @classmethod
    async def get_pool_status(cls) -> Dict[str, Dict[str, Any]]:
        """Get status of all connection pools"""
        status = {}
        for service, pool in cls._pools.items():
            status[service] = {
                "size": pool.get_size(),
                "min_size": pool.get_min_size(), 
                "max_size": pool.get_max_size(),
                "idle_size": pool.get_idle_size(),
                "environment": cls._environment
            }
        return status

class ConnectionPoolMonitor:
    """Monitor connection pool performance and health"""
    
    @staticmethod
    async def monitor_pool_health(pool: asyncpg.Pool, service: str) -> Dict[str, Any]:
        """Monitor individual pool health"""
        try:
            # Test connection
            async with pool.acquire() as conn:
                # Simple health check query
                result = await conn.fetchval("SELECT 1")
                
            return {
                "service": service,
                "status": "healthy" if result == 1 else "unhealthy",
                "pool_size": pool.get_size(),
                "idle_connections": pool.get_idle_size(),
                "max_size": pool.get_max_size(),
                "min_size": pool.get_min_size()
            }
        except Exception as e:
            logger.error(f"Pool health check failed for {service}", error=str(e))
            return {
                "service": service,
                "status": "error",
                "error": str(e)
            }
    
    @staticmethod
    async def get_database_stats(pool: asyncpg.Pool) -> Dict[str, Any]:
        """Get database performance statistics"""
        try:
            async with pool.acquire() as conn:
                # Get connection count
                conn_stats = await conn.fetchrow("""
                    SELECT count(*) as total_connections,
                           count(*) FILTER (WHERE state = 'active') as active_connections,
                           count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                """)
                
                # Get database size
                db_size = await conn.fetchval("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """)
                
                # Get slow queries count
                slow_queries = await conn.fetchval("""
                    SELECT count(*) 
                    FROM pg_stat_statements 
                    WHERE mean_exec_time > 1000
                """) if await conn.fetchval("SELECT count(*) FROM pg_extension WHERE extname = 'pg_stat_statements'") else 0
                
                return {
                    "total_connections": conn_stats["total_connections"],
                    "active_connections": conn_stats["active_connections"], 
                    "idle_connections": conn_stats["idle_connections"],
                    "database_size": db_size,
                    "slow_queries_count": slow_queries
                }
        except Exception as e:
            logger.error("Failed to get database stats", error=str(e))
            return {"error": str(e)}

# Example usage and configuration
ENVIRONMENT_DATABASE_CONFIGS = {
    "development": {
        "api_gateway": "postgresql://saasctl_dev_pro1_user:dev_password@47.79.87.199:5432/saascontrol_dev_pro1",
        "data_service": "postgresql://saasctl_dev_pro1_user:dev_password@47.79.87.199:5432/saascontrol_dev_pro1",
        "ai_service": "postgresql://saasctl_dev_pro2_user:dev_password@47.79.87.199:5432/saascontrol_dev_pro2"
    },
    "staging": {
        "api_gateway": "postgresql://saasctl_stage_pro1_user:stage_password@47.79.87.199:5432/saascontrol_stage_pro1",
        "data_service": "postgresql://saasctl_stage_pro1_user:stage_password@47.79.87.199:5432/saascontrol_stage_pro1", 
        "ai_service": "postgresql://saasctl_stage_pro2_user:stage_password@47.79.87.199:5432/saascontrol_stage_pro2"
    },
    "production": {
        "api_gateway": "postgresql://saasctl_prod_pro1_user:prod_password@47.79.87.199:5432/saascontrol_prod_pro1",
        "data_service": "postgresql://saasctl_prod_pro1_user:prod_password@47.79.87.199:5432/saascontrol_prod_pro1",
        "ai_service": "postgresql://saasctl_prod_pro2_user:prod_password@47.79.87.199:5432/saascontrol_prod_pro2"
    }
}

async def initialize_database_pools(environment: str = "development"):
    """Initialize database pools for the specified environment"""
    config = ENVIRONMENT_DATABASE_CONFIGS.get(environment)
    if not config:
        raise ValueError(f"No configuration found for environment: {environment}")
    
    await OptimizedDatabase.initialize_pools(environment, config)
    logger.info(f"Database pools initialized for environment: {environment}")

async def health_check_all_pools():
    """Run health checks on all initialized pools"""
    monitor = ConnectionPoolMonitor()
    results = []
    
    for service in OptimizedDatabase._pools.keys():
        pool = OptimizedDatabase.get_pool(service)
        health = await monitor.monitor_pool_health(pool, service)
        stats = await monitor.get_database_stats(pool)
        
        results.append({
            "service": service,
            "health": health,
            "stats": stats
        })
    
    return results

if __name__ == "__main__":
    # Example initialization
    async def main():
        await initialize_database_pools("development")
        health_results = await health_check_all_pools()
        
        for result in health_results:
            print(f"Service: {result['service']}")
            print(f"Health: {result['health']}")
            print(f"Stats: {result['stats']}")
            print("-" * 50)
        
        await OptimizedDatabase.close_all_pools()
    
    asyncio.run(main())