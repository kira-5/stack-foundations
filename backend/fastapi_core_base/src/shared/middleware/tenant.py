from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from src.shared.db.core.tenant_context import TenantContext

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts the tenant ID from the 'X-Tenant-ID' header
    and sets it in the global TenantContext for the duration of the request.
    """
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        tenant_id = request.headers.get("X-Tenant-ID")
        
        # Set the tenant context using the context manager
        with TenantContext.tenant_scope(tenant_id):
            response = await call_next(request)
            
            # Optional: Add the tenant ID back to the response header for debugging
            if tenant_id:
                response.headers["X-Tenant-ID"] = tenant_id
                
            return response
