"""
Cernji-Logging Python Usage Example

This file demonstrates how to use Cernji-Logging in a Python application.
Copy relevant sections to your application.
"""

import asyncio
from cernji_logging import (
    get_logger,
    with_correlation_id,
    set_correlation_id,
    get_correlation_id,
    generate_correlation_id,
    timed,
    TimingContext,
)

# ============================================
# Basic Logger Setup
# ============================================

# Get a logger for your module
# The logger name appears in logs as 'event.module'
logger = get_logger(__name__)


# ============================================
# Basic Logging Examples
# ============================================

def basic_logging_example():
    """Basic logging with structured data"""

    # Info level with extra fields
    logger.info("Application started", version="1.0.0", config="loaded")

    # Debug level (only appears if LOG_LEVEL=DEBUG)
    logger.debug("Detailed diagnostic info", variable="value")

    # Warning level
    logger.warning("Unusual condition detected", condition="rate_limit")

    # Error level with exception info
    try:
        raise ValueError("Example error")
    except Exception as e:
        logger.error("Operation failed", error=str(e), exc_info=True)


# ============================================
# Correlation ID Examples
# ============================================

async def correlation_id_example():
    """Using correlation IDs for distributed tracing"""

    # Generate a new correlation ID
    correlation_id = generate_correlation_id()

    # Use context manager (recommended for async code)
    with with_correlation_id(correlation_id):
        logger.info("Processing request")  # Will include trace.id
        await some_async_operation()
        logger.info("Request completed")   # Will include same trace.id

    # Alternative: Set globally (use carefully in async code)
    set_correlation_id(correlation_id)
    logger.info("This also has trace.id")

    # Get current correlation ID
    current_id = get_correlation_id()
    logger.info("Current correlation ID", trace_id=current_id)


# ============================================
# HTTP Request Example
# ============================================

async def http_endpoint_example(request):
    """Example FastAPI/Flask endpoint with correlation ID"""

    # Extract correlation ID from header or generate new one
    correlation_id = request.headers.get('X-Correlation-ID') or generate_correlation_id()

    with with_correlation_id(correlation_id):
        logger.info("HTTP request received",
                   method=request.method,
                   path=request.url.path)

        try:
            result = await process_request(request)
            logger.info("HTTP request completed", status=200)
            return result
        except Exception as e:
            logger.error("HTTP request failed",
                        error=str(e),
                        exc_info=True)
            raise


# ============================================
# Service-to-Service Communication
# ============================================

async def call_external_service():
    """Propagate correlation ID to external services"""
    import httpx

    # Get current correlation ID
    correlation_id = get_correlation_id()

    # Build headers with correlation ID
    headers = {}
    if correlation_id:
        headers['X-Correlation-ID'] = correlation_id

    logger.info("Calling external service", service="api.example.com")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://api.example.com/data',
            headers=headers
        )

    logger.info("External service response", status=response.status_code)
    return response


# ============================================
# Performance Timing Examples
# ============================================

@timed(logger)
async def timed_function_example():
    """Function decorator for automatic timing (default: info level)"""
    await asyncio.sleep(0.1)  # Simulate work
    return "result"


@timed(logger, level="debug")
async def timed_function_debug():
    """Function decorator with custom log level"""
    await asyncio.sleep(0.05)
    return "result"


async def timing_context_example():
    """Manual timing using context manager"""

    # Time a specific block of code
    with TimingContext(logger, "database_query"):
        await asyncio.sleep(0.2)  # Simulate database query
        # Duration automatically logged when context exits

    # Time multiple operations
    with TimingContext(logger, "cache_check"):
        await asyncio.sleep(0.01)


# ============================================
# Class-Based Example
# ============================================

class UserService:
    """Example service class with logging"""

    def __init__(self):
        self.logger = get_logger(f"{__name__}.UserService")

    @timed(logger)
    async def create_user(self, user_data: dict):
        """Create a user with logging and timing"""
        correlation_id = generate_correlation_id()

        with with_correlation_id(correlation_id):
            self.logger.info("Creating user", email=user_data.get("email"))

            try:
                # Simulate user creation
                await asyncio.sleep(0.1)
                user_id = "user_123"

                self.logger.info("User created successfully",
                               user_id=user_id,
                               email=user_data.get("email"))
                return user_id

            except Exception as e:
                self.logger.error("User creation failed",
                                error=str(e),
                                email=user_data.get("email"),
                                exc_info=True)
                raise

    async def get_user(self, user_id: str):
        """Get user with timing context"""
        with TimingContext(self.logger, "get_user"):
            self.logger.debug("Fetching user", user_id=user_id)

            # Simulate database query
            await asyncio.sleep(0.05)

            return {"id": user_id, "name": "John Doe"}


# ============================================
# Migration Example
# ============================================

def migration_before():
    """OLD CODE: Using print statements"""
    user_id = "user_123"
    print(f"Processing user {user_id}")
    print(f"User {user_id} processed successfully")


def migration_after():
    """NEW CODE: Using Cernji-Logging"""
    user_id = "user_123"
    logger.info("Processing user", user_id=user_id)
    logger.info("User processed successfully", user_id=user_id)


# ============================================
# Complete Application Example
# ============================================

async def main():
    """Complete example showing all features"""

    # 1. Basic logging
    logger.info("Application starting", version="1.0.0")

    # 2. Generate correlation ID for this session
    session_id = generate_correlation_id()

    with with_correlation_id(session_id):
        # 3. Timed operation
        result = await timed_function_example()

        # 4. Use service class
        service = UserService()
        user_id = await service.create_user({
            "email": "user@example.com",
            "name": "John Doe"
        })

        # 5. Call external service (propagates correlation ID)
        # await call_external_service()

        logger.info("Application session complete", user_id=user_id)


# ============================================
# Helper Functions
# ============================================

async def some_async_operation():
    """Dummy async operation"""
    await asyncio.sleep(0.01)


async def process_request(request):
    """Dummy request processor"""
    await asyncio.sleep(0.05)
    return {"status": "success"}


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
