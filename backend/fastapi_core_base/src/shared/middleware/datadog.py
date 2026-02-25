# app/extensions/datadog_middleware.py
import json
import os
import time
import traceback
from collections.abc import Callable

from ddtrace.trace import tracer
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class DatadogTracingMiddleware(BaseHTTPMiddleware):
    """
    Production-grade Datadog tracing middleware for FastAPI with:
    - Request/response timing
    - Error tracking
    - Custom metadata tagging
    - Configurable sampling
    - Body content capture (optional)
    - Header propagation
    """

    # ============================================================================
    # TOGGLE FLAG: Set this to True/False to switch span creation strategy
    # ============================================================================
    # True  = Create custom span (better hierarchy, cleaner grouping) - RECOMMENDED
    # False = Use FastAPI auto-instrumentation span (no duplicates, flatter view)
    USE_CUSTOM_SPAN = True
    # ============================================================================

    def __init__(
        self,
        app: ASGIApp,
        service_name: str = "fastapi-app",
        sample_body_content: bool = False,
        sample_rate: float = 1.0,
        trace_headers: list | None = None,
    ):
        """Initialize middleware.

        :param app: ASGI application
        :param service_name: Service name in Datadog
        :param sample_body_content: Whether to capture request/response
            bodies
        :param sample_rate: Percentage of requests to trace (0.1 = 10%)
        :param trace_headers: List of headers to capture
        """
        super().__init__(app)
        self.service_name = service_name
        self.sample_body_content = sample_body_content
        self.sample_rate = min(1.0, max(0.0, sample_rate))
        self.trace_headers = trace_headers or [
            "x-request-id",
            "x-correlation-id",
            "user-agent",
            "x-forwarded-for",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip tracing based on sample rate
        if self._should_skip_tracing(request):
            return await call_next(request)

        # Start request processing
        start_time = time.time()

        # Choose span creation strategy based on class flag
        if self.USE_CUSTOM_SPAN:
            # Approach 1: Create custom span (better hierarchy, cleaner grouping)
            span = self._start_span(request)
        else:
            # Approach 2: Use FastAPI auto-instrumentation span (no duplicates, but flatter view)
            span = tracer.current_span()
            if not span:
                # Fallback: if no span exists, create one
                span = self._start_span(request)
            else:
                # Enhance the existing span
                self._enhance_span(span, request)

        response = None

        try:
            # Process request with tracing
            response = await self._process_request_with_tracing(
                request,
                call_next,
                span,
                start_time,
            )

            # Mark errors based on HTTP status code (for Error Tracking)
            # This ensures 4xx/5xx responses appear in Error Tracking even if no exception was raised
            if response and hasattr(response, "status_code"):
                span.set_tag("http.status_code", response.status_code)

                # Add success/failure tags based on status code
                if 200 <= response.status_code < 400:
                    span.set_tag("request.status", "success")
                elif response.status_code >= 400:
                    span.set_tag("request.status", "failure")
                    span.set_tag("error", True)
                    span.set_tag("error.type", f"HTTP_{response.status_code}")
                    span.set_tag("error.message", f"HTTP {response.status_code} Error")

                    # Set severity based on status code
                    if response.status_code >= 500:
                        span.set_tag("error.severity", "high")
                    elif response.status_code >= 400:
                        span.set_tag("error.severity", "medium")

                    # Try to extract error message from response body if available
                    try:
                        if hasattr(response, "body") and response.body:
                            # Try to parse JSON error response
                            import json

                            if isinstance(response.body, bytes):
                                body_str = response.body.decode(
                                    "utf-8",
                                    errors="ignore",
                                )
                            else:
                                body_str = str(response.body)
                            try:
                                error_data = json.loads(body_str)
                                if "detail" in error_data:
                                    span.set_tag(
                                        "error.message",
                                        str(error_data["detail"])[:500],
                                    )
                                elif "message" in error_data:
                                    span.set_tag(
                                        "error.message",
                                        str(error_data["message"])[:500],
                                    )
                            except (json.JSONDecodeError, ValueError):
                                # If not JSON, use first 500 chars of body
                                span.set_tag("error.message", body_str[:500])
                    except Exception:
                        pass

                # Add response size if available
                if hasattr(response, "body") and response.body:
                    try:
                        span.set_metric("http.response.size", len(response.body))
                    except Exception:
                        pass

            return response

        except Exception as e:
            self._handle_exception(span, e, start_time)
            raise

        finally:
            # Always set response time metric
            response_time = time.time() - start_time
            span.set_metric("http.response_time", response_time)

            # Track error rate metrics per endpoint/service
            self._track_error_rate_metrics(span, request, response)

            # Add business context tags from request state if available
            self._add_business_context_tags(span, request)

            # Finish span only if we created it (custom span approach)
            if self.USE_CUSTOM_SPAN:
                span.finish()
            # Otherwise, let FastAPI auto-instrumentation handle span lifecycle

    def _should_skip_tracing(self, request: Request) -> bool:
        """Determine if we should skip tracing for this request."""
        return self.sample_rate < 1.0 and hash(request.url.path) % 100 > self.sample_rate * 100

    def _start_span(self, request: Request):
        """Create a custom Datadog span for the request with correct service name.

        This approach provides better hierarchy and trace grouping in
        Datadog.
        """
        # Normalize route name for better grouping in Datadog
        # All APIs have prefix /base-pricing/api/v1, after which endpoint varies
        # Example: /base-pricing/api/v1/strategies/123 → /base-pricing/api/v1/strategies/{id}
        normalized_route = self._normalize_route_path(request.url.path)
        resource = f"{request.method} {normalized_route}"

        # Create span with correct service name (from DD_SERVICE via self.service_name)
        # This ensures no duplicate services and proper hierarchy
        span = tracer.trace(
            "fastapi.request",
            service=self.service_name,  # Uses DD_SERVICE value
            resource=resource,
            span_type="web",
        )

        # CRITICAL: Set trace context in ASGI scope to prevent warnings
        # This ensures the trace context is available throughout the request lifecycle
        # ddtrace.contrib.asgi looks for the span in the scope to propagate context
        try:
            # Store the span in the ASGI scope using the key that ddtrace.contrib.asgi expects
            # This prevents the "datadog context not present in ASGI request scope" warning
            request.scope["ddtrace_asgi.span"] = span
            # Also store it in the standard location for ASGI middleware
            if "ddtrace" not in request.scope:
                request.scope["ddtrace"] = {}
            request.scope["ddtrace"]["span"] = span
        except Exception:
            # If setting scope fails, continue anyway - span will still work
            pass

        # Set standard HTTP tags
        self._set_basic_tags(span, request)

        # Add custom headers to span
        self._capture_headers(span, request)

        return span

    def _enhance_span(self, span, request: Request):
        """Enhance the existing FastAPI auto-instrumentation span with custom tags."""
        # Ensure the span uses the correct service name (from DD_SERVICE)
        # This prevents duplicate services in Datadog
        if self.service_name:
            span.service = self.service_name

        # Normalize route name for better grouping in Datadog
        # All APIs have prefix /base-pricing/api/v1, after which endpoint varies
        # Example: /base-pricing/api/v1/strategies/123 → /base-pricing/api/v1/strategies/{id}
        normalized_route = self._normalize_route_path(request.url.path)

        # Update resource name for better grouping
        resource = f"{request.method} {normalized_route}"
        span.resource = resource

        # Set standard HTTP tags
        self._set_basic_tags(span, request)

        # Add custom headers to span
        self._capture_headers(span, request)

    def _normalize_route_path(self, path: str) -> str:
        """Normalize route path by replacing IDs with placeholders.

        All APIs have the prefix `/base-pricing/api/v1`, after which the endpoint varies.
        This function normalizes IDs in the endpoint part while preserving the prefix.

        Examples:
        - /base-pricing/api/v1/strategies/123 → /base-pricing/api/v1/strategies/{id}
        - /base-pricing/api/v1/strategies/456 → /base-pricing/api/v1/strategies/{id}
        - /base-pricing/api/v1/products/789 → /base-pricing/api/v1/products/{id}
        - /base-pricing/api/v1/strategies/123/plans/456 → /base-pricing/api/v1/strategies/{id}/plans/{id}

        :param path: Original path like "/base-pricing/api/v1/strategies/123"
        :return: Normalized path like "/base-pricing/api/v1/strategies/{id}"
        """
        import re

        # Common API prefix (all routes have this)
        api_prefix = "/base-pricing/api/v1"

        # If path doesn't start with prefix, normalize the whole path
        if not path.startswith(api_prefix):
            normalized = path
        else:
            # Split into prefix and endpoint
            endpoint = path[len(api_prefix) :]
            # Normalize only the endpoint part (after prefix)
            normalized_endpoint = endpoint
            # Common patterns to normalize (apply in order)
            patterns = [
                # UUIDs first (most specific)
                (
                    r"/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
                    "/{uuid}",
                ),
                # MD5 hashes
                (r"/[a-f0-9]{32}", "/{hash}"),
                # Numeric IDs (most common, apply last)
                (r"/\d+", "/{id}"),
            ]

            for pattern, replacement in patterns:
                normalized_endpoint = re.sub(pattern, replacement, normalized_endpoint)

            # Reconstruct with prefix
            normalized = api_prefix + normalized_endpoint

        return normalized

    async def _process_request_with_tracing(
        self,
        request: Request,
        call_next: Callable,
        span,
        start_time: float,
    ) -> Response:
        """Process request with tracing context."""
        try:
            # Optionally capture request body
            if self.sample_body_content:
                await self._capture_request_body(span, request)

            # Process request
            response = await call_next(request)

            # Optionally capture error responses
            if self.sample_body_content and response.status_code >= 400:
                self._capture_response_body(span, response)

            return response

        except Exception as e:
            self._handle_exception(span, e, start_time)
            raise

    def _set_basic_tags(self, span, request: Request) -> None:
        """Set standard HTTP and framework tags."""
        span.set_tag("http.method", request.method)
        span.set_tag("http.url", str(request.url))
        span.set_tag("http.route", request.url.path)

        # Add normalized route name for better grouping
        normalized_route = self._normalize_route_path(request.url.path)
        span.set_tag("http.route_name", normalized_route)

        span.set_tag("http.host", request.url.hostname)
        if request.url.query:
            span.set_tag("http.query.string", request.url.query)
        span.set_tag("component", "fastapi")
        span.set_tag("span.kind", "server")

        # Environment tag
        span.set_tag("env", os.getenv("DD_ENV", "development"))

        # Add service version if available
        service_version = os.getenv("DD_VERSION")
        if service_version:
            span.set_tag("version", service_version)

        # Add global tags directly to span for visibility in Datadog UI
        # These tags help filter/search traces by client, environment, application, server
        # Get values directly from environment or config
        try:
            from src.shared.configuration.config import env_config_manager

            # Get dynamic values
            client = env_config_manager.get_dynamic_setting("CLIENT_NAME", None)
            application = env_config_manager.get_dynamic_setting("APPLICATION", None)
            env = getattr(
                env_config_manager.environment_settings,
                "DEPLOYMENT_ENV",
                os.getenv("DD_ENV", None),
            )
            server = "be"  # Backend identifier

            # Set tags directly on span
            tags_set = []
            if client:
                span.set_tag("client", str(client))
                tags_set.append(f"client:{client}")
            if application:
                span.set_tag("application", str(application))
                tags_set.append(f"application:{application}")
            if env:
                span.set_tag("env", str(env))
                tags_set.append(f"env:{env}")
            span.set_tag("server", server)
            tags_set.append(f"server:{server}")

            # Debug: Log tags being set (remove after verification)
            if tags_set:
                print(f"🔖 Setting Datadog tags on span: {', '.join(tags_set)}")

            # Also try parsing DD_TAGS as fallback
            dd_tags = os.getenv("DD_TAGS", "")
            if dd_tags:
                for tag_pair in dd_tags.split(","):
                    if ":" in tag_pair:
                        key, value = tag_pair.split(":", 1)
                        span.set_tag(key.strip(), value.strip())
        except Exception:
            # Fallback: just parse DD_TAGS if config is not available
            dd_tags = os.getenv("DD_TAGS", "")
            if dd_tags:
                for tag_pair in dd_tags.split(","):
                    if ":" in tag_pair:
                        key, value = tag_pair.split(":", 1)
                        span.set_tag(key.strip(), value.strip())

    def _capture_headers(self, span, request: Request) -> None:
        """Extract and tag headers."""
        for header in self.trace_headers:
            if header in request.headers:
                clean_header = header.replace("-", "_").lower()
                span.set_tag(f"http.header.{clean_header}", request.headers[header])

    async def _capture_request_body(self, span, request: Request) -> None:
        """Safely capture request body content."""
        try:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type.lower():
                body = await request.json()
                span.set_tag(
                    "http.request.body",
                    json.dumps(body, default=str)[:1000],
                )  # Truncate
        except Exception as e:
            span.set_tag("http.request.body.error", str(e))

    def _capture_response_body(self, span, response: Response) -> None:
        """Safely capture error response body."""
        try:
            body = getattr(response, "body", "")
            if body:
                span.set_tag("http.response.body", str(body)[:1000])  # Truncate
        except Exception as e:
            span.set_tag("http.response.body.error", str(e))

    def _handle_exception(self, span, exception: Exception, start_time: float) -> None:
        """Record exception details with full stack trace."""
        span.set_tag("request.status", "failure")
        span.set_tag("error", True)
        span.set_tag("error.message", str(exception))
        span.set_tag("error.type", type(exception).__name__)
        span.set_metric("http.response_time", time.time() - start_time)

        # Add full stack trace
        try:
            exc_traceback = traceback.format_exc()
            # Truncate to avoid exceeding Datadog tag limits (25KB)
            span.set_tag("error.stack", exc_traceback[:20000])
        except Exception:
            pass

        # Mark 5xx errors specifically
        status_code = getattr(exception, "status_code", None)
        if status_code is not None:
            if status_code >= 500:
                span.set_tag("error.severity", "high")
            elif status_code >= 400:
                span.set_tag("error.severity", "medium")
            else:
                span.set_tag("error.severity", "low")
        else:
            span.set_tag("error.severity", "low")

    def _add_business_context_tags(self, span, request: Request) -> None:
        """Extract and add business context tags from multiple sources."""
        try:
            # Extract user_id from multiple sources (priority order)
            user_id = None
            # 1. Try request state (set by CustomRouteHandler after authentication)
            if hasattr(request.state, "user_id") and request.state.user_id:
                user_id = request.state.user_id
            # 2. Try headers
            elif request.headers.get("user-id"):
                user_id = request.headers.get("user-id")
            # 3. Try query params
            elif hasattr(request, "query_params") and request.query_params.get(
                "user_id",
            ):
                user_id = request.query_params.get("user_id")

            if user_id:
                span.set_tag("user.id", str(user_id))

            # Extract tenant_id from multiple sources (priority order)
            tenant_id = None
            # 1. Try request state (set by middleware/route handler)
            if hasattr(request.state, "tenant_id") and request.state.tenant_id:
                tenant_id = request.state.tenant_id
            # 2. Try headers
            elif request.headers.get("x-tenant-id"):
                tenant_id = request.headers.get("x-tenant-id")
            # 3. Try query params
            elif hasattr(request, "query_params") and request.query_params.get(
                "tenant_id",
            ):
                tenant_id = request.query_params.get("tenant_id")
            # 4. Try to extract from URL hostname (e.g., lesliespool.devs.impactsmartsuite.com)
            elif request.url.hostname:
                hostname_parts = request.url.hostname.split(".")
                if len(hostname_parts) > 0 and hostname_parts[0] not in [
                    "www",
                    "api",
                    "devs",
                    "staging",
                    "prod",
                ]:
                    tenant_id = hostname_parts[0]
            # 5. Try config (fallback)
            if not tenant_id:
                try:
                    from src.shared.configuration.config import env_config_manager

                    tenant_id = env_config_manager.get_dynamic_setting("TENANT_ID")
                except Exception:
                    pass

            if tenant_id:
                span.set_tag("tenant.id", str(tenant_id))

            # Try to extract business context from path parameters
            if hasattr(request, "path_params"):
                # Extract strategy_id if present
                strategy_id = request.path_params.get("strategy_id")
                if strategy_id:
                    span.set_tag("strategy.id", str(strategy_id))

                # Extract plan_id if present
                plan_id = request.path_params.get("plan_id")
                if plan_id:
                    span.set_tag("plan.id", str(plan_id))

                # Extract product_id if present
                product_id = request.path_params.get("product_id")
                if product_id:
                    span.set_tag("product.id", str(product_id))

                # Extract store_id if present
                store_id = request.path_params.get("store_id")
                if store_id:
                    span.set_tag("store.id", str(store_id))

            # Extract model_type from query params if present
            if hasattr(request, "query_params"):
                model_type = request.query_params.get("model_type")
                if model_type:
                    span.set_tag("model.type", model_type)

                view_type = request.query_params.get("view_type")
                if view_type:
                    span.set_tag("view.type", view_type)

                session_id = request.query_params.get("session_id")
                if session_id:
                    span.set_tag("session.id", session_id)

            # Extract request ID from headers
            request_id = request.headers.get("x-request-id") or request.headers.get(
                "x-correlation-id",
            )
            if request_id:
                span.set_tag("request.id", request_id)

        except Exception:
            # Don't fail the request if tagging fails
            pass

    def _track_error_rate_metrics(
        self,
        span,
        request: Request,
        response: Response | None,
    ) -> None:
        """Track error rate metrics per endpoint/service for monitoring and alerting.

        This adds custom metrics that help track:
        - Total request count per endpoint (http.requests.total)
        - Error count per endpoint (http.requests.error)
        - Success count per endpoint (http.requests.success)

        Datadog automatically calculates error rate as: error_rate = errors / total
        These metrics can be used in Datadog dashboards, monitors, and alerts.

        Example queries in Datadog:
        - sum:http.requests.error{*} / sum:http.requests.total{*} (overall error rate)
        - sum:http.requests.error{endpoint:/api/strategies} / sum:http.requests.total{endpoint:/api/strategies}
        """
        try:
            # Get normalized route for consistent tracking
            normalized_route = self._normalize_route_path(request.url.path)

            # Determine if this is an error (4xx or 5xx status code)
            is_error = False
            status_code = None
            if response and hasattr(response, "status_code"):
                status_code = response.status_code
                if status_code is not None:
                    is_error = status_code >= 400

            # Get service name
            service_name = self.service_name or os.getenv("DD_SERVICE", "fastapi-app")

            # Track total requests count (counter metric - always 1 per request)
            # Datadog will sum these to get total request count
            span.set_metric("http.requests.total", 1.0)
            span.set_tag("metric.endpoint", normalized_route)
            span.set_tag("metric.method", request.method)
            span.set_tag("metric.service", service_name)

            # Track error requests count (counter metric - 1 if error, 0 otherwise)
            if is_error and status_code is not None:
                span.set_metric("http.requests.error", 1.0)
                span.set_tag("metric.error_type", f"HTTP_{status_code}")
                span.set_tag(
                    "metric.error_category",
                    "server_error" if status_code >= 500 else "client_error",
                )
            else:
                span.set_metric("http.requests.error", 0.0)

            # Track success requests count (counter metric - 1 if success, 0 otherwise)
            if not is_error:
                span.set_metric("http.requests.success", 1.0)
            else:
                span.set_metric("http.requests.success", 0.0)

            # Add status code as tag for filtering/grouping
            if status_code:
                span.set_tag("metric.status_code", str(status_code))
                span.set_tag("metric.status_class", f"{status_code // 100}xx")

        except Exception:
            # Don't fail the request if metric tracking fails
            pass
