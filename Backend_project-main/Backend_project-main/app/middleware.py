import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from .logger import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", "-")
        logger.bind(request_id=request_id, method=request.method, path=request.url.path).info("request_start")
        start_time = time.time()
        try:
            response: Response = await call_next(request)
        except Exception as e:
            logger.bind(request_id=request_id, error=str(e)).error("request_error")
            raise
        process_time = (time.time() - start_time) * 1000
        logger.bind(request_id=request_id, status_code=response.status_code, duration_ms=process_time).info("request_end")
        return response
