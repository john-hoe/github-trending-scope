# 本地预览服务器：模拟 Cloudflare Pages 的干净网址（/index-zh、/repos/x/），支持视频 Range 请求，禁用缓存。
import http.server, socketserver, os, sys, re, mimetypes
port, root = int(sys.argv[1]), os.path.expanduser(sys.argv[2])
class H(http.server.BaseHTTPRequestHandler):
    def resolve(self):
        p = self.path.split('?')[0].split('#')[0]
        p = os.path.normpath('/' + p.lstrip('/'))
        for cand in (p, p + '.html', os.path.join(p, 'index.html')):
            f = os.path.realpath(os.path.join(root, cand.lstrip('/')))
            if os.path.isfile(f): return f
        return None
    def send(self, head):
        f = self.resolve()
        if not f:
            f404 = os.path.join(root, '404.html'); self.send_response(404); self.send_header('Content-Type', 'text/html; charset=utf-8')
            body = open(f404, 'rb').read() if os.path.exists(f404) else b'not found'; self.send_header('Content-Length', str(len(body))); self.end_headers()
            if not head: self.wfile.write(body)
            return
        size = os.path.getsize(f); ctype = mimetypes.guess_type(f)[0] or 'application/octet-stream'
        if f.endswith('.vtt'): ctype = 'text/vtt; charset=utf-8'
        if ctype.startswith('text/') and 'charset' not in ctype: ctype += '; charset=utf-8'
        start, end, code = 0, size - 1, 200
        m = re.match(r'bytes=(\d*)-(\d*)', self.headers.get('Range', ''))
        if m and (m.group(1) or m.group(2)):
            if m.group(1): start = int(m.group(1)); end = int(m.group(2)) if m.group(2) else end
            else: start = max(0, size - int(m.group(2)))
            end = min(end, size - 1); code = 206
        self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Accept-Ranges', 'bytes'); self.send_header('Cache-Control', 'no-store')
        self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Content-Length', str(end - start + 1))
        if code == 206: self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        if head: return
        with open(f, 'rb') as fh:
            fh.seek(start); left = end - start + 1
            while left > 0:
                chunk = fh.read(min(65536, left))
                if not chunk: break
                try: self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError): break
                left -= len(chunk)
    def do_GET(self): self.send(False)
    def do_HEAD(self): self.send(True)
    def log_message(self, *a): pass
socketserver.ThreadingTCPServer.allow_reuse_address = True
socketserver.ThreadingTCPServer(('0.0.0.0', port), H).serve_forever()
