from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class FallbackCORSHeadersMiddleware(MiddlewareMixin):
    """Fallback middleware that sets explicit CORS headers when the response
    doesn't include them. Use only as a last resort if the edge/proxy rewrites
    headers to '*' or strips Access-Control-Allow-Credentials.

    It will set Access-Control-Allow-Origin to the incoming Origin header if
    the origin is in settings.CORS_ALLOWED_ORIGINS and will set
    Access-Control-Allow-Credentials: true.
    """

    def process_response(self, request, response):
        origin = request.headers.get('Origin')
        if not origin:
            return response

        allowed = getattr(settings, 'CORS_ALLOWED_ORIGINS', []) or []
        # Normalize allowed list
        allowed = [a.rstrip('/') for a in allowed]

        if origin.rstrip('/') in allowed:
            # Only set if the response doesn't already include credentials header
            if 'Access-Control-Allow-Credentials' not in response:
                response['Access-Control-Allow-Credentials'] = 'true'
            # If wildcard origin is present, replace it with the explicit origin
            aco = response.get('Access-Control-Allow-Origin')
            if aco == '*' or not aco:
                response['Access-Control-Allow-Origin'] = origin

            # Ensure Access-Control-Expose-Headers exists if not set
            if 'Access-Control-Expose-Headers' not in response:
                response['Access-Control-Expose-Headers'] = 'Content-Type, Authorization'

        return response
