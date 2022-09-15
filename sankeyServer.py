import urllib.parse
import http.server
import re
from pathlib import Path

HOST = ('0.0.0.0', '2003')
pattern = re.compile('.html', re.IGNORECASE)


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url_parts = urllib.parse.urlparse(self.path)
        request_file_path = Path(url_parts.path.strip("/"))

        ext = request_file_path.suffix
        if not request_file_path.is_file() and not pattern.match(ext):
            return

        return http.server.SimpleHTTPRequestHandler.do_GET(self)
