"""
HTTP Server - custom request handler with regex-based router.

Implements a stateless HTTP request handler that routes to application handlers.
Session tokens are parsed from cookies (simple UUID format).
"""

import re
import json
import uuid
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from io import BytesIO


class Route:
    """Single route definition: method + path pattern -> handler"""

    def __init__(self, method: str, path_pattern: str, handler):
        """
        Args:
            method: HTTP method ('GET', 'POST', 'PUT', 'DELETE', etc.)
            path_pattern: Regex pattern for path matching (e.g., r'^/grids/(\d+)$')
            handler: Callable that handles the request
        """
        self.method = method.upper()
        self.path_pattern = re.compile(path_pattern)
        self.handler = handler

    def matches(self, method: str, path: str):
        """Check if this route matches the request method and path"""
        return self.method == method.upper() and self.path_pattern.match(path)

    def extract_params(self, path: str):
        """Extract regex capture groups from path"""
        match = self.path_pattern.match(path)
        return match.groups() if match else ()


class Router:
    """Regex-based HTTP router"""

    def __init__(self):
        self.routes = []

    def add_route(self, method: str, path_pattern: str, handler):
        """Register a route"""
        self.routes.append(Route(method, path_pattern, handler))

    def find_route(self, method: str, path: str):
        """Find matching route for method + path, returning (route, path_params)"""
        for route in self.routes:
            if route.matches(method, path):
                params = route.extract_params(path)
                return route, params
        return None, ()

    def get_handler(self, method: str, path: str):
        """Get handler for method + path, or None if not found"""
        route, _ = self.find_route(method, path)
        return route.handler if route else None


class RequestHandler(BaseHTTPRequestHandler):
    """Custom HTTP request handler for the crossword API"""

    # Class-level router (set by start_server)
    router = None

    # Class-level app container (set by start_server)
    app = None

    def do_GET(self):
        """Handle GET request"""
        self._handle_request("GET")

    def do_POST(self):
        """Handle POST request"""
        self._handle_request("POST")

    def do_PUT(self):
        """Handle PUT request"""
        self._handle_request("PUT")

    def do_DELETE(self):
        """Handle DELETE request"""
        self._handle_request("DELETE")

    def _handle_request(self, method: str):
        """Route and handle request"""
        # Parse URL
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_string = parsed_url.query

        # Parse query parameters
        query_params = {}
        if query_string:
            query_dict = parse_qs(query_string)
            # parse_qs returns lists; convert to single values
            query_params = {k: v[0] if len(v) == 1 else v for k, v in query_dict.items()}

        # Parse body (for POST/PUT)
        body = None
        body_params = {}
        if method in ("POST", "PUT"):
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length:
                body_bytes = self.rfile.read(content_length)
                body = body_bytes.decode("utf-8")
                try:
                    body_params = json.loads(body)
                except json.JSONDecodeError:
                    body_params = {}

        # Parse session token from cookies
        session_token = self._parse_session_token()

        # Find route
        route, path_params = self.router.find_route(method, path)
        if not route:
            self._send_error(404, "Not Found")
            return

        # Call handler
        try:
            handler = route.handler
            response = handler(
                path_params=path_params,
                query_params=query_params,
                body_params=body_params,
                session_token=session_token,
                request_handler=self,
                app=self.app,
            )

            # Send response (skip if handler already sent it and returned None)
            if response is None:
                pass  # Handler already sent the response
            elif isinstance(response, dict):
                self._send_json(response)
            elif isinstance(response, bytes):
                self._send_bytes(response)
            else:
                self._send_text(str(response))

        except Exception as e:
            self._send_error(500, str(e))

    def _parse_session_token(self):
        """Extract session token from Cookie header"""
        cookie_header = self.headers.get("Cookie", "")
        if not cookie_header:
            return None

        # Parse cookies (simple format: key=value; key=value)
        for cookie in cookie_header.split(";"):
            cookie = cookie.strip()
            if "=" in cookie:
                key, value = cookie.split("=", 1)
                if key.strip() == "session":
                    return value.strip()
        return None

    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response"""
        response_body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(response_body))
        self.end_headers()
        self.wfile.write(response_body)

    def _send_bytes(self, data: bytes, status: int = 200, content_type: str = "application/octet-stream"):
        """Send binary response"""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, text: str, status: int = 200):
        """Send text response"""
        response_body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", len(response_body))
        self.end_headers()
        self.wfile.write(response_body)

    def _send_error(self, status: int, message: str):
        """Send error response as JSON"""
        self._send_json({"error": message}, status=status)

    def log_message(self, format, *args):
        """Suppress default request logging"""
        pass


def create_server(port: int = 8000, host: str = "127.0.0.1"):
    """
    Create and configure HTTP server.

    Args:
        port: Port to listen on
        host: Host to bind to

    Returns:
        (server, router) tuple ready for start_server()
    """
    from http.server import HTTPServer

    router = Router()

    # Create server instance
    server = HTTPServer((host, port), RequestHandler)

    # Attach router to request handler
    RequestHandler.router = router

    return server, router


def start_server(server, router, app_container, host: str = "127.0.0.1", port: int = 8000):
    """
    Start the HTTP server with wired app container.

    Args:
        server: HTTPServer instance from create_server()
        router: Router instance from create_server()
        app_container: AppContainer from wiring.make_app()
        host: Host for logging
        port: Port for logging
    """
    # Attach app to request handler
    RequestHandler.app = app_container

    print(f"Starting HTTP server on http://{host}:{port}")
    print(f"Registered routes: {len(router.routes)}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()
