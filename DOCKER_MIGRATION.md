# Docker Migration Summary

## Changes Made

### 1. Added Redis to Docker Compose (`docker-compose.yml`)

**Added Redis Service:**
```yaml
redis:
  image: redis:7-alpine
  container_name: ringshell-redis
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: redis-server --appendonly yes
  restart: unless-stopped
```

**Updated Backend Service:**
- Added Redis environment variables
- Added `depends_on: redis` to ensure Redis starts first
- Redis hostname is `redis` within Docker network

**Added Volume:**
```yaml
volumes:
  redis_data:
    driver: local
```

### 2. Fixed `wti_news.py` for Docker

**Removed:**
- ❌ Parent directory path manipulation (`sys.path.insert`)
- ❌ Non-existent `DataBase_Connection_Source.RedisDatabaseStorage` import

**Added:**
- ✅ Proper Redis client using `redis` library
- ✅ Environment variable configuration
- ✅ Docker-friendly imports (no path hacks)

**New Redis Client Function:**
```python
def get_redis_client():
    """Create and return a Redis client using environment variables."""
    redis_config = {
        "host": os.getenv("RINGSHELL_REDIS_HOST", "localhost"),
        "port": int(os.getenv("RINGSHELL_REDIS_PORT", 6379)),
        "decode_responses": True
    }
    
    # Add auth if provided
    username = os.getenv("RINGSHELL_REDIS_USERNAME")
    password = os.getenv("RINGSHELL_REDIS_PASSWORD")
    
    if username:
        redis_config["username"] = username
    if password:
        redis_config["password"] = password
    
    return redis.Redis(**redis_config)
```

**Updated Redis Operations:**
- `redis_client.get_json()` → `json.loads(redis_client.get())`
- `redis_client.store_json()` → `redis_client.set(key, json.dumps(data))`

### 3. Environment Variables

The following environment variables are now used:

**Required:**
- `RINGSHELL_FMP_API_KEY` - Financial Modeling Prep API key

**Redis (Auto-configured in Docker):**
- `RINGSHELL_REDIS_HOST=redis` (default: localhost)
- `RINGSHELL_REDIS_PORT=6379`
- `RINGSHELL_REDIS_USERNAME=` (optional)
- `RINGSHELL_REDIS_PASSWORD=` (optional)

### 4. Documentation

Created `backend/src/financial/data_sources/README.md` with:
- Module overview
- Redis configuration guide
- Docker setup instructions
- Usage examples
- Data structure documentation

## How to Use

### Start Services

```bash
# Start Redis and backend
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Connect to Redis CLI

```bash
# From host
docker exec -it ringshell-redis redis-cli

# Check stored data
> KEYS Crude_Oil:*
> GET Crude_Oil:NEWS:WTI:new
```

### Run Backend Commands

```bash
# Enter backend container
docker exec -it ringshell-backend bash

# Test the news fetcher
python -c "from src.financial.data_sources import get_wti_news; print(len(get_wti_news()))"
```

## Benefits

1. **No Path Hacks**: Clean imports using `PYTHONPATH=/app`
2. **Redis Integration**: Proper caching layer for news data
3. **Environment-Based Config**: Easy to switch between dev/staging/prod
4. **Docker Native**: Services communicate via Docker network
5. **Persistent Storage**: Redis data survives container restarts
6. **Production Ready**: Follows Docker best practices

## Testing

To test the changes:

```bash
# 1. Ensure .env file exists with required keys
cp .env.example .env
# Edit .env and add your RINGSHELL_FMP_API_KEY

# 2. Start services
docker-compose up -d

# 3. Check Redis is running
docker exec -it ringshell-redis redis-cli ping
# Should return: PONG

# 4. Test news fetcher inside backend container
docker exec -it ringshell-backend python -c "
from src.financial.data_sources.wti_news import get_wti_news
news = get_wti_news(days_back=7)
print(f'Fetched {len(news)} articles')
"

# 5. Verify data in Redis
docker exec -it ringshell-redis redis-cli GET "Crude_Oil:NEWS:WTI:new"
```

## Migration Notes

- All existing code using `wti_news.py` will work without changes
- The function signature remains the same: `get_wti_news(days_back: int = 730) -> list`
- Redis keys structure is preserved
- The module is backward compatible with local development (uses `localhost` by default)

