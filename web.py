import socket
import time
import network
import errno
import uasyncio

class Route:
    def __init__(self, path: str, methods: list[str], function, *function_args) -> None:
        self.path: str = path
        self.methods: list[str] = methods
        self.function = function
        self.function_args = function_args

    def check(self, request: Request):
        return request.path == self.path and request.method in self.methods

class WifiConfig:
    def __init__(self, ssid: str, password: str, timeout: int = 10, raise_on_connection_failure: bool = False) -> None:
        self.ssid: str = ssid
        self.password: str = password
        self.timeout: int = timeout
        self.raise_on_connection_failure: bool = raise_on_connection_failure

class Request:
    def __init__(self, request_obj: str | bytes) -> None:
        if isinstance(request_obj, bytes):
            self.request_str: str = request_obj.decode()
        else:
            self.request_str: str = request_obj

        lines = list(filter(None, self.request_str.splitlines()))
        request_line, *header_lines = lines

        self.method = request_line.split(' ')[0]
        self.path = request_line.split(' ')[1]
        self.protocol = request_line.split(' ')[2]
        self.header = dict([i.split(': ', 1) for i in header_lines])

class Web:
    def __init__(self, wifi_config: WifiConfig | None = None) -> None:
        self._routes: list[Route] = []
        self.wifi_config = wifi_config

    def route(self, path: str, **kwargs):
        def inner(function):
            self._routes.append(Route(path, kwargs.get('methods', ['GET']), function))

        return inner

    async def serve(self, host: str, port: int):
        wlan = network.WLAN(network.STA_IF)

        def connect_to_wifi(wifi_config: WifiConfig | None) -> str:
            if not wifi_config:
                return host

            ssid, password, timeout, raise_on_failure = wifi_config.ssid, wifi_config.password, wifi_config.timeout, wifi_config.raise_on_connection_failure

            wlan.active(True)
            wlan.connect(ssid, password)

            wait = timeout
            while not wlan.isconnected():
                if wait == 0:
                    if raise_on_failure:
                        raise ConnectionError(f"Cannot connect to wifi network with ssid='{ssid}' and password='{password}'.")

                    break

                wait -= 1
                time.sleep(1)

            status = wlan.ifconfig()
            return status[0]

        ip = connect_to_wifi(self.wifi_config)

        addr = socket.getaddrinfo(host, port)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setblocking(False)
        s.bind(addr)
        s.listen(1)

        print(f'Web server running on {host}:{port}')
        print(f'        http://{ip}:{port}')

        while True:
            if wlan.isconnected():
                try:
                    conn, addr = s.accept()
                    conn.settimeout(2.0)
                    print(f'Connection from {addr[0]}:{addr[1]}')

                    def serve_response(payload: str, code: str = '200 OK', content_type: str = 'text/html'):
                        conn.send(f'HTTP/1.0 {code}\r\nContent-type: {content_type}\r\n\r\n'.encode())
                        conn.send(payload.encode())
                        conn.close()

                    raw_req = conn.recv(1024)
                    request = Request(raw_req)
                    print(f'[{addr[0]}] Request: {raw_req}')
                    for route in self._routes:
                        if route.check(request):
                            r = route.function(*route.function_args)

                            if isinstance(r, str):
                                serve_response(r)
                            else:
                                serve_response(*r)

                            break

                    else:
                        serve_response(f'<h2>404 - Not found {request.path}</h2>', '404')

                except OSError as e:
                    if e.args[0] == errno.EAGAIN:
                        pass
                    else:
                        print(f"Failed to serve (socket error): {e}")

                except Exception as e:
                    print(f"Failed to serve: {e}")

            else:
                connect_to_wifi(self.wifi_config)

            await uasyncio.sleep(0.1)
