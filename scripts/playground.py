"""Serve the NanoGPU playground on loopback and run requests through RTL."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
import webbrowser


HTML = Path(__file__).with_suffix('.html')
PHOTOS = HTML.parent.parent / 'docs' / 'assets'


def integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{label} must be an integer from {low} to {high}.')
    return value


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('Expected a request object.')
    mode = data.get('mode')
    if mode == 'mac':
        groups = data.get('groups')
        if not isinstance(groups, list) or not 1 <= len(groups) <= 255:
            raise ValueError('Enter between 1 and 255 operand groups.')
        for index, group in enumerate(groups, 1):
            if not isinstance(group, list) or len(group) != 4:
                raise ValueError(f'Group {index} needs four operands: a₀, b₀, a₁, b₁.')
            for value in group:
                integer(value, -128, 127, f'Group {index} operand')
    elif mode == 'edges':
        width = integer(data.get('width'), 3, 64, 'Photo width')
        height = integer(data.get('height'), 3, 64, 'Photo height')
        pixels = data.get('pixels')
        if not isinstance(pixels, list) or len(pixels) != width * height:
            raise ValueError('Send one brightness value per photo pixel.')
        for value in pixels:
            integer(value, 0, 255, 'Pixel brightness')
    elif mode == 'draw':
        integer(data.get('background'), 0, 255, 'Background')
        layers = data.get('layers')
        if not isinstance(layers, list) or not 1 <= len(layers) <= 6:
            raise ValueError('Add between 1 and 6 rectangles.')
        for index, layer in enumerate(layers, 1):
            label = f'Rectangle {index}'
            if not isinstance(layer, dict):
                raise ValueError(f'{label} must describe a rectangle.')
            x = integer(layer.get('x'), 0, 63, f'{label} x')
            y = integer(layer.get('y'), 0, 63, f'{label} y')
            integer(layer.get('width'), 1, 64 - x, f'{label} width')
            integer(layer.get('height'), 1, 64 - y, f'{label} height')
            program = layer.get('program')
            if not isinstance(program, list) or not 1 <= len(program) <= 4:
                raise ValueError(f'{label} needs one to four instructions.')
            for opcode in program:
                integer(opcode, 0, 6, f'{label} graphics opcode')
    else:
        raise ValueError('Choose edge detection, graphics, or MAC compute.')


def serve(simulate, *, open_browser):
    assets = {
        '/': ('text/html; charset=utf-8', HTML.read_bytes()),
        '/samples/coins.png': ('image/png', (PHOTOS / 'edge-coins.png').read_bytes()),
        '/samples/coffee.png': ('image/png', (PHOTOS / 'edge-coffee.png').read_bytes()),
    }
    lock = Lock()

    class Handler(BaseHTTPRequestHandler):
        def send_content(self, status, content_type, content):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(content)

        def send_json(self, status, data):
            self.send_content(status, 'application/json', json.dumps(data).encode('utf-8'))

        def do_GET(self):
            if self.headers.get('Host') != host or self.path not in assets:
                self.send_error(404)
                return
            self.send_content(200, *assets[self.path])

        def do_POST(self):
            if self.headers.get('Host') != host or self.path != '/simulate':
                self.send_error(404)
                return
            if self.headers.get('Origin', url) != url:
                self.send_json(403, {'error': 'Open the playground from the address printed in the terminal.'})
                return
            if self.headers.get_content_type() != 'application/json':
                self.send_json(415, {'error': 'Expected a JSON request.'})
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 32_768:
                    raise ValueError('The request has an invalid size.')
                data = json.loads(self.rfile.read(size))
                validate(data)
            except (ValueError, RecursionError) as error:
                self.send_json(400, {'error': str(error)})
                return

            if not lock.acquire(blocking=False):
                self.send_json(409, {'error': 'A simulation is already running. Try again in a moment.'})
                return
            try:
                with TemporaryDirectory(prefix='nanogpu-playground-') as directory:
                    run_dir = Path(directory)
                    request = run_dir / 'request.json'
                    request.write_text(json.dumps(data), encoding='utf-8')
                    simulate(test_module='playground_job', run_dir=run_dir,
                             extra_env={'NANOGPU_PLAYGROUND_REQUEST': str(request)})
                    result = json.loads((run_dir / 'response.json').read_text(encoding='utf-8'))
            except (Exception, SystemExit) as error:
                # Cocotb runners can exit with SystemExit on a simulator failure.
                print(f'Playground simulation failed: {error}', flush=True)
                self.send_json(500, {'error': 'The RTL simulation failed. Check the playground terminal.'})
                return
            finally:
                lock.release()
            self.send_json(200, result)

    with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        host = f'127.0.0.1:{server.server_port}'
        url = f'http://{host}'
        print(f'NanoGPU Playground: {url}\nPress Ctrl+C to stop it.', flush=True)
        if open_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nPlayground stopped.', flush=True)
