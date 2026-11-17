import io
import sys

SERVER_RESPONSE_200_OK = b"HTTP/1.1 200 OK\r\n\r\n"


class Socket:
    def __init__(self, read_data=SERVER_RESPONSE_200_OK):
        self._write_buffer = io.BytesIO()
        self._read_buffer = io.BytesIO(read_data)
        self.timeout = None
        self.closed = False

    def connect(self, address):
        pass

    def settimeout(self, timeout):
        self.timeout = timeout

    def write(self, buf):
        self._write_buffer.write(buf)

    def readline(self):
        return self._read_buffer.readline()

    def read(self, size=-1):
        return self._read_buffer.read(size)

    def readinto(self, buf):
        return self._read_buffer.readinto(buf)

    def close(self):
        self.closed = True


class socket:
    AF_INET = 2
    SOCK_STREAM = 1
    IPPROTO_TCP = 6

    @staticmethod
    def getaddrinfo(host, port, af=0, type=0, flags=0):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", 80))]

    def socket(af=AF_INET, type=SOCK_STREAM, proto=IPPROTO_TCP):
        return Socket()


sys.modules["socket"] = socket


class SSLContext:
    def __init__(self, protocol=None):
        self.protocol = protocol
        self.verify_mode = None
        self.wrapped = []

    def wrap_socket(self, sock, server_hostname=None):
        self.wrapped.append(server_hostname)
        return sock


class tls:
    PROTOCOL_TLS_CLIENT = 0
    CERT_NONE = 0
    CERT_REQUIRED = 2
    contexts = []

    @staticmethod
    def SSLContext(protocol):
        context = SSLContext(protocol)
        tls.contexts.append(context)
        return context


sys.modules["tls"] = tls
# ruff: noqa: E402
import requests


def format_message(response):
    return response.raw._write_buffer.getvalue().decode("utf8")


def test_simple_get():
    response = requests.request("GET", "http://example.com")

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n" + b"Connection: close\r\n" + b"Host: example.com\r\n\r\n"
    ), format_message(response)


def test_get_query_anchor():
    response = requests.request("GET", "http://example.com?query")
    assert response.raw._write_buffer.getvalue() == (
        b"GET /?query HTTP/1.1\r\nConnection: close\r\nHost: example.com\r\n\r\n"
    ), format_message(response)

    response = requests.request("GET", "http://example.com#anchor")
    assert response.raw._write_buffer.getvalue() == (
        b"GET /#anchor HTTP/1.1\r\nConnection: close\r\nHost: example.com\r\n\r\n"
    ), format_message(response)


def test_get_auth():
    response = requests.request(
        "GET", "http://example.com", auth=("test-username", "test-password")
    )

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n"
        + b"Host: example.com\r\n"
        + b"Authorization: Basic dGVzdC11c2VybmFtZTp0ZXN0LXBhc3N3b3Jk\r\n"
        + b"Connection: close\r\n\r\n"
    ), format_message(response)


def test_get_custom_header():
    response = requests.request("GET", "http://example.com", headers={"User-Agent": "test-agent"})

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n"
        + b"User-Agent: test-agent\r\n"
        + b"Host: example.com\r\n"
        + b"Connection: close\r\n\r\n"
    ), format_message(response)


def test_post_json():
    response = requests.request("GET", "http://example.com", json="test")

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n"
        + b"Connection: close\r\n"
        + b"Content-Type: application/json\r\n"
        + b"Host: example.com\r\n"
        + b"Content-Length: 6\r\n\r\n"
        + b'"test"'
    ), format_message(response)


def test_post_json_unicode():
    response = requests.request("POST", "http://example.com", json="aαbβcγdδ")  # noqa: RUF001

    assert response.raw._write_buffer.getvalue() == (
        b"POST / HTTP/1.1\r\n"
        b"Connection: close\r\n"
        b"Content-Type: application/json\r\n"
        b"Host: example.com\r\n"
        b"Content-Length: 14\r\n\r\n" + bytes('"aαbβcγdδ"', "utf-8")  # noqa: RUF001
    ), format_message(response)


def test_post_data_str():
    response = requests.request("POST", "http://example.com", data="body")

    assert response.raw._write_buffer.getvalue() == (
        b"POST / HTTP/1.1\r\n"
        b"Content-Length: 4\r\n"
        b"Host: example.com\r\n"
        b"Connection: close\r\n\r\n"
        b"body"
    ), format_message(response)


def test_post_data_str_unicode():
    response = requests.request("POST", "http://example.com", data="aαbβcγdδ")  # noqa: RUF001

    assert response.raw._write_buffer.getvalue() == (
        b"POST / HTTP/1.1\r\n"
        b"Content-Length: 12\r\n"
        b"Host: example.com\r\n"
        b"Connection: close\r\n\r\n" + bytes("aαbβcγdδ", "utf-8")  # noqa: RUF001
    ), format_message(response)


def test_post_data_bytes():
    response = requests.request("POST", "http://example.com", data=b"body\x01\x02\x03\xff")

    assert response.raw._write_buffer.getvalue() == (
        b"POST / HTTP/1.1\r\n"
        b"Content-Length: 8\r\n"
        b"Host: example.com\r\n"
        b"Connection: close\r\n\r\n"
        b"body\x01\x02\x03\xff"
    ), response.raw._write_buffer.getvalue()


def test_post_chunked_data():
    def chunks():
        yield "test"

    response = requests.request("GET", "http://example.com", data=chunks())

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n"
        + b"Transfer-Encoding: chunked\r\n"
        + b"Host: example.com\r\n"
        + b"Connection: close\r\n\r\n"
        + b"4\r\ntest\r\n"
        + b"0\r\n\r\n"
    ), format_message(response)


def test_overwrite_get_headers():
    response = requests.request(
        "GET", "http://example.com", headers={"Host": "test.com", "Connection": "keep-alive"}
    )

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n" + b"Connection: keep-alive\r\n" + b"Host: test.com\r\n\r\n"
    ), format_message(response)


def test_overwrite_post_json_headers():
    response = requests.request(
        "GET",
        "http://example.com",
        json="test",
        headers={"Content-Type": "text/plain", "Content-Length": "10"},
    )

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n"
        + b"Connection: close\r\n"
        + b"Content-Length: 10\r\n"
        + b"Content-Type: text/plain\r\n"
        + b"Host: example.com\r\n\r\n"
        + b'"test"'
    ), format_message(response)


def test_overwrite_post_chunked_data_headers():
    def chunks():
        yield "test"

    response = requests.request(
        "GET", "http://example.com", data=chunks(), headers={"Content-Length": "4"}
    )

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n"
        + b"Host: example.com\r\n"
        + b"Content-Length: 4\r\n"
        + b"Connection: close\r\n\r\n"
        + b"test"
    ), format_message(response)


def test_do_not_modify_headers_argument():
    global do_not_modify_this_dict
    do_not_modify_this_dict = {}
    requests.request("GET", "http://example.com", headers=do_not_modify_this_dict)

    assert do_not_modify_this_dict == {}, do_not_modify_this_dict


def test_content_length_via_content():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello"
    )
    response = requests.request("GET", "http://example.com")
    assert response.content == b"hello"
    assert response.headers["Content-Length"] == "5"
    socket.socket = lambda *a, **k: Socket()


def test_chunked_response_via_content():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n6\r\n world\r\n0\r\n\r\n"
    )
    response = requests.request("GET", "http://example.com")
    assert response.content == b"hello world"
    socket.socket = lambda *a, **k: Socket()


def test_chunked_response_readinto():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n3\r\nabc\r\n4\r\ndefg\r\n0\r\n\r\n"
    )
    response = requests.request("GET", "http://example.com")
    buf = bytearray(2)
    result = b""
    while True:
        n = response.raw.readinto(buf)
        if n == 0:
            break
        result += buf if n == 2 else buf[:n]
    assert result == b"abcdefg"
    socket.socket = lambda *a, **k: Socket()


def test_raw_open_before_content():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello"
    )
    response = requests.request("GET", "http://example.com")
    assert response.raw is not None
    assert response.raw.read(1) == b"h"
    socket.socket = lambda *a, **k: Socket()


def test_raw_incremental_content_length():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 10\r\n\r\nabcdefghij"
    )
    response = requests.request("GET", "http://example.com")
    assert response.raw.read(3) == b"abc"
    assert response.raw.read(3) == b"def"
    assert response.content == b"ghij"
    assert response.raw is None
    socket.socket = lambda *a, **k: Socket()


def test_raw_readinto_content_length():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 10\r\n\r\nabcdefghij"
    )
    response = requests.request("GET", "http://example.com")
    buf = bytearray(3)
    result = b""
    while True:
        n = response.raw.readinto(buf)
        if n == 0:
            break
        result += buf if n == 3 else buf[:n]
    assert result == b"abcdefghij"
    socket.socket = lambda *a, **k: Socket()


def test_https_without_ssl_skips_verification():
    tls.contexts.clear()

    requests.request("GET", "https://example.com")

    assert len(tls.contexts) == 1
    assert tls.contexts[0].verify_mode == tls.CERT_NONE
    assert tls.contexts[0].wrapped == ["example.com"]


def test_https_wraps_with_the_given_ssl_context():
    tls.contexts.clear()
    context = SSLContext()
    context.verify_mode = tls.CERT_REQUIRED

    requests.get("https://example.com:8443/x", ssl=context)

    assert tls.contexts == []
    assert context.wrapped == ["example.com"]
    assert context.verify_mode == tls.CERT_REQUIRED


def test_redirect_keeps_the_ssl_context():
    server = iter(
        [
            b"HTTP/1.1 302 Found\r\nLocation: https://other.example.com/next\r\n\r\n",
            SERVER_RESPONSE_200_OK,
        ]
    )
    socket.socket = lambda *a, **k: Socket(next(server))
    context = SSLContext()

    requests.get("https://example.com", ssl=context)

    assert context.wrapped == ["example.com", "other.example.com"]

    socket.socket = lambda *a, **k: Socket()


def test_errors_close_the_socket():
    class RaisingContext:
        def __init__(self, exc):
            self.exc = exc

        def wrap_socket(self, s, server_hostname=None):
            raise self.exc

    # A failed verification raises ValueError; running out of memory, MemoryError;
    # a value that isn't a context, AttributeError.
    for ssl, exc_type in (
        (RaisingContext(ValueError("certificate verify failed")), ValueError),
        (RaisingContext(MemoryError()), MemoryError),
        (True, AttributeError),
    ):
        sock = Socket()
        closed = []
        sock.close = lambda: closed.append(True)
        socket.socket = lambda *a, **k: sock

        try:
            requests.get("https://example.com", ssl=ssl)
        except exc_type:
            pass
        else:
            assert False, "expected %s" % exc_type

        assert closed == [True], exc_type

    socket.socket = lambda *a, **k: Socket()


def test_ssl_refuses_an_http_url():
    made = []
    socket.socket = lambda *a, **k: made.append(1) or Socket()

    try:
        requests.get("http://example.com", ssl=SSLContext())
    except ValueError:
        pass
    else:
        assert False, "expected ValueError"

    assert made == []

    socket.socket = lambda *a, **k: Socket()


def test_ssl_refuses_a_redirect_to_http():
    first = Socket(b"HTTP/1.1 302 Found\r\nLocation: http://example.com/next\r\n\r\n")
    closed = []
    first.close = lambda: closed.append(True)
    made = []

    def make(*a, **k):
        made.append(1)
        return first

    socket.socket = make
    context = SSLContext()

    try:
        requests.get("https://example.com", ssl=context)
    except ValueError:
        pass
    else:
        assert False, "expected ValueError"

    assert context.wrapped == ["example.com"]
    assert closed == [True]
    assert made == [1]

    socket.socket = lambda *a, **k: Socket()


def test_redirect_absolute():
    server = iter(
        [
            b"HTTP/1.1 301 OK\r\nLocation: http://example.com/index\r\n\r\n",
            SERVER_RESPONSE_200_OK,
        ]
    )
    socket.socket = lambda *a, **k: Socket(next(server))

    response = requests.request("GET", "http://example.com")

    assert response.raw._write_buffer.getvalue() == (
        b"GET /index HTTP/1.1\r\nConnection: close\r\nHost: example.com\r\n\r\n"
    ), format_message(response)

    socket.socket = lambda *a, **k: Socket()


def test_redirect_relative():
    server = iter(
        [
            b"HTTP/1.1 301 OK\r\nLocation: /index\r\n\r\n",
            SERVER_RESPONSE_200_OK,
        ]
    )
    socket.socket = lambda *a, **k: Socket(next(server))

    response = requests.request("GET", "http://example.com")

    assert response.raw._write_buffer.getvalue() == (
        b"GET /index HTTP/1.1\r\nConnection: close\r\nHost: example.com\r\n\r\n"
    ), format_message(response)

    socket.socket = lambda *a, **k: Socket()


def test_chunked_response_lowercase_header():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\ntransfer-encoding: chunked\r\n\r\n5\r\nhello\r\n6\r\n world\r\n0\r\n\r\n"
    )
    response = requests.request("GET", "http://example.com")
    assert response.content == b"hello world"
    socket.socket = lambda *a, **k: Socket()


def test_redirect_lowercase_location():
    server = iter(
        [
            b"HTTP/1.1 301 OK\r\nlocation: /index\r\n\r\n",
            SERVER_RESPONSE_200_OK,
        ]
    )
    socket.socket = lambda *a, **k: Socket(next(server))

    response = requests.request("GET", "http://example.com")

    assert response.raw._write_buffer.getvalue() == (
        b"GET /index HTTP/1.1\r\nConnection: close\r\nHost: example.com\r\n\r\n"
    ), format_message(response)

    socket.socket = lambda *a, **k: Socket()


def serve(*responses):
    # Each socket made reads the next response. Returns the sockets made.
    sockets = []
    responses = iter(responses)

    def make(*a, **k):
        sockets.append(Socket(next(responses)))
        return sockets[-1]

    socket.socket = make
    return sockets


def sent(sockets):
    return [s._write_buffer.getvalue() for s in sockets]


def found(location):
    return b"HTTP/1.1 302 Found\r\nLocation: " + location + b"\r\n\r\n"


def test_redirect_auth_stays_on_the_same_origin():
    # As in CPython requests, Authorization is kept only when the scheme, host
    # and port stay the same, or from http to https on the default ports.
    for url, location, kept in (
        ("http://example.com", b"/next", True),
        ("http://example.com", b"http://example.com:80/next", True),
        ("https://example.com:443", b"https://example.com/next", True),
        ("http://example.com", b"https://example.com/next", True),
        ("http://example.com", b"http://other.example.com/next", False),
        ("http://example.com", b"https://other.example.com/next", False),
        ("http://example.com", b"http://example.com:8080/next", False),
        ("http://example.com", b"https://example.com:8443/next", False),
        ("http://example.com:8080", b"https://example.com/next", False),
        ("https://example.com", b"http://example.com/next", False),
        ("https://example.com", b"https://example.com:8443/next", False),
    ):
        sockets = serve(found(location), SERVER_RESPONSE_200_OK)
        requests.get(url, auth=("user", "pass"))
        first, second = sent(sockets)
        assert b"Authorization: Basic" in first, first
        assert (b"Authorization" in second) == kept, (url, location, second)

    # Each redirect is judged against the request it came from, and once
    # dropped, Authorization stays dropped, from auth= or from headers=.
    for kw, chain, kept in (
        (
            {"auth": ("user", "pass")},
            (b"https://example.com/", b"http://example.com/"),
            [True, True, False],
        ),
        (
            {"auth": ("user", "pass")},
            (b"http://other.example.com/", b"/again"),
            [True, False, False],
        ),
        (
            {"headers": {"Authorization": "Bearer token"}},
            (b"http://other.example.com/", b"http://example.com/"),
            [True, False, False],
        ),
    ):
        sockets = serve(*[found(l) for l in chain] + [SERVER_RESPONSE_200_OK])
        requests.get("http://example.com", **kw)
        assert [b"Authorization" in s for s in sent(sockets)] == kept, (kw, chain)

    socket.socket = lambda *a, **k: Socket()


def test_redirect_keeps_timeout_and_parse_headers():
    sockets = serve(found(b"/next"), b"HTTP/1.1 200 OK\r\nX-Final: 1\r\n\r\n")
    lines = []

    requests.get("http://example.com", timeout=2, parse_headers=lambda l, d: lines.append(l))

    assert [s.timeout for s in sockets] == [2, 2], [s.timeout for s in sockets]
    assert lines == [b"Location: /next\r\n", b"X-Final: 1\r\n"], lines

    serve(found(b"/next"), SERVER_RESPONSE_200_OK)
    assert not hasattr(requests.get("http://example.com", parse_headers=False), "headers")

    socket.socket = lambda *a, **k: Socket()


def test_redirect_to_get_drops_the_body_headers():
    def chunks():
        yield "body"

    for status in (b"301", b"302", b"303"):
        for kw in (
            {"data": "body"},
            {"json": {"a": 1}},
            {"data": chunks()},
            {"data": "body", "headers": {"Content-Type": "text/plain"}},
        ):
            sockets = serve(
                b"HTTP/1.1 " + status + b" Moved\r\nLocation: /next\r\n\r\n",
                SERVER_RESPONSE_200_OK,
            )
            requests.post("http://example.com", **kw)
            second = sent(sockets)[1]
            assert second.startswith(b"GET /next HTTP/1.1\r\n"), second
            assert second.endswith(b"\r\n\r\n"), second
            for name in (b"Content-Length", b"Content-Type", b"Transfer-Encoding"):
                assert name not in second, (status, kw, second)

    socket.socket = lambda *a, **k: Socket()


def test_redirect_keeps_head():
    # As in CPython requests, a 301, 302 or 303 doesn't turn HEAD into GET.
    for status in (b"301", b"302", b"303"):
        sockets = serve(
            b"HTTP/1.1 " + status + b" Moved\r\nLocation: /next\r\n\r\n",
            b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\n",
        )
        response = requests.head("http://example.com")
        assert sent(sockets)[1].startswith(b"HEAD /next HTTP/1.1\r\n"), sent(sockets)[1]
        assert response.content == b"", response.content

    socket.socket = lambda *a, **k: Socket()


def test_redirect_307_and_308_resend_json():
    for status in (b"307", b"308"):
        sockets = serve(
            b"HTTP/1.1 " + status + b" Temporary Redirect\r\nLocation: /next\r\n\r\n",
            SERVER_RESPONSE_200_OK,
        )
        requests.post("http://example.com", json={"a": 1})
        first, second = sent(sockets)
        assert second.startswith(b"POST /next HTTP/1.1\r\n"), second
        assert b"Content-Type: application/json\r\n" in second, second
        assert b"Content-Length: 8\r\n" in second, second
        assert second.endswith(b'\r\n\r\n{"a": 1}'), second

    socket.socket = lambda *a, **k: Socket()


def test_redirect_limit():
    # As in CPython requests, follow at most 30 redirects.
    loop = found(b"/loop")
    sockets = []
    socket.socket = lambda *a, **k: sockets.append(Socket(loop)) or sockets[-1]
    try:
        requests.get("http://example.com")
    except ValueError:
        pass
    else:
        assert False, "expected ValueError"
    assert len(sockets) == 31, len(sockets)
    assert all(s.closed for s in sockets)

    sockets = serve(*([loop] * 30 + [SERVER_RESPONSE_200_OK]))
    assert requests.get("http://example.com").status_code == 200
    assert len(sockets) == 31, len(sockets)

    socket.socket = lambda *a, **k: Socket()


def test_redirect_lets_go_of_the_socket():
    # The socket of a redirect response mustn't be kept while the redirect is
    # followed: over TLS, each one holds memory.
    import gc

    free = []

    def make(*a, **k):
        gc.collect()
        free.append(gc.mem_free())
        s = Socket(SERVER_RESPONSE_200_OK if len(free) > 10 else found(b"/"))
        s.ballast = bytearray(64000)
        return s

    socket.socket = make
    requests.get("http://example.com")
    assert free[0] - free[-1] < 192000, free

    socket.socket = lambda *a, **k: Socket()


def test_head_has_no_body():
    for header in (b"Content-Length: 5\r\n", b"Transfer-Encoding: chunked\r\n"):
        socket.socket = lambda *a, **k: Socket(b"HTTP/1.1 200 OK\r\n" + header + b"\r\n")
        response = requests.head("http://example.com")
        assert response.content == b"", response.content

    socket.socket = lambda *a, **k: Socket()


def test_content_length_lowercase_header():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\ncontent-length: 5\r\n\r\nhello"
    )
    response = requests.request("GET", "http://example.com")
    assert response.content == b"hello"
    assert response.headers["content-length"] == "5"
    socket.socket = lambda *a, **k: Socket()


test_simple_get()
test_get_query_anchor()
test_get_auth()
test_get_custom_header()
test_post_json()
test_post_json_unicode()
test_post_data_str()
test_post_data_str_unicode()
test_post_data_bytes()
test_post_chunked_data()
test_https_without_ssl_skips_verification()
test_https_wraps_with_the_given_ssl_context()
test_redirect_keeps_the_ssl_context()
test_errors_close_the_socket()
test_ssl_refuses_an_http_url()
test_ssl_refuses_a_redirect_to_http()
test_overwrite_get_headers()
test_overwrite_post_json_headers()
test_overwrite_post_chunked_data_headers()
test_do_not_modify_headers_argument()
test_content_length_via_content()
test_chunked_response_via_content()
test_chunked_response_readinto()
test_raw_open_before_content()
test_raw_incremental_content_length()
test_raw_readinto_content_length()
test_redirect_absolute()
test_redirect_relative()
test_chunked_response_lowercase_header()
test_redirect_lowercase_location()
test_redirect_auth_stays_on_the_same_origin()
test_redirect_keeps_timeout_and_parse_headers()
test_redirect_to_get_drops_the_body_headers()
test_redirect_keeps_head()
test_redirect_307_and_308_resend_json()
test_redirect_limit()
test_redirect_lets_go_of_the_socket()
test_head_has_no_body()
test_content_length_lowercase_header()
