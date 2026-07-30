Start Docker dev environment and verify container health.

Steps:
1. Run `docker compose up -d` to start all services
2. Wait 5 seconds for containers to initialize
3. Run `docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"` to show container status
4. Check if key containers are healthy:
   - `luana-dev-{brand}_backend_dev-1` (backend)
   - `luana-dev-{brand}_frontend_dev-1` (frontend)
   - `luana-dev-luana_postgres_dev-1` (database, shared)
   - `luana_redis_dev` (cache)
5. Report any containers that are not running or unhealthy
