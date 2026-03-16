import logging
import time

security_logger = logging.getLogger("security")

class SecurityAuditMiddleware:

    SENSITIVE_PATHS = ("/api/v1/alerts/", "/api/v1/readings/", "/api/v1/auth/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        if response.status_code == 401:
            security_logger.warning(
                "UNAUTHORIZED path=%s method=%s ip=%s",
                request.path,
                request.method,
                self._get_client_ip(request),
            )
        elif response.status_code == 403:
            security_logger.warning(
                "FORBIDDEN path=%s method=%s ip=%s user=%s",
                request.path,
                request.method,
                self._get_client_ip(request),
                getattr(request.user, "username", "anonymous"),
            )
        elif request.method in ("PATCH", "POST", "DELETE") and response.status_code < 400:
            security_logger.warning(
                "WRITE_OP path=%s method=%s status=%s user=%s ip=%s duration_ms=%d",
                request.path,
                request.method,
                response.status_code,
                getattr(request.user, "username", "anonymous"),
                self._get_client_ip(request),
                duration_ms,
            )

        return response

    @staticmethod
    def _get_client_ip(request) -> str:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
