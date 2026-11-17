import datetime
import hashlib
import json
import os
import re
import secrets
import socket
import ssl
import struct
import tempfile
import time
import unicodedata
from pathlib import Path, PureWindowsPath

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

PORT = 43872
MAGIC = "lan-folder-sync-v1"
LIMIT = 16 * 1024 * 1024

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def scan(root):
    files = {}

    def visit(folder):
        for path in folder.iterdir():
            if path.name in {".DS_Store", "Thumbs.db", "desktop.ini"} or path.name.startswith((".lan-sync-", "._")):
                continue
            if path.is_symlink() or getattr(path.lstat(), "st_file_attributes", 0) & 1024:
                continue
            if path.is_dir():
                visit(path)
            elif path.is_file():
                rel = path.relative_to(root)
                key = unicodedata.normalize("NFC", rel.as_posix()).casefold()
                if key in files:
                    raise ValueError(f"文件名冲突：{rel}")
                files[key] = (rel, digest(path))
    visit(root)
    return files




def tls_server():
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "LAN Sync")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(minutes=1))
            .not_valid_after(now + datetime.timedelta(days=7)).sign(key, hashes.SHA256()))
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    with tempfile.TemporaryDirectory() as folder:
        pem = Path(folder) / "identity.pem"
        pem.write_bytes(cert.public_bytes(serialization.Encoding.PEM) + key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()))
        ctx.load_cert_chain(pem)
    return ctx


def tls_client():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def exact(sock, size):
    data = bytearray()
    while len(data) < size:
        block = sock.recv(min(1024 * 128, size - len(data)))
        if not block:
            raise ConnectionError("对方已断开")
        data.extend(block)
    return data


def send(sock, value):
    data = json.dumps(value).encode()
    if len(data) > LIMIT:
        raise ValueError("目录清单过大")
    sock.sendall(struct.pack("!I", len(data)) + data)


def read(sock):
    size, = struct.unpack("!I", exact(sock, 4))
    if size > LIMIT:
        raise ValueError("消息过大")
    return json.loads(exact(sock, size))


def location(root, rel):
    path = root
    for part in rel.split("/"):
        if (not part or part in {".", ".."} or part.endswith((" ", "."))
                or re.search(r'[<>:"\\|?*\x00-\x1f]', part)
                or PureWindowsPath(part).is_reserved() or part.lower().startswith(".lan-sync-")):
            raise ValueError(f"不兼容的文件名：{rel}")
        path = path / part
        if path.is_symlink() or (path.exists() and getattr(path.lstat(), "st_file_attributes", 0) & 1024):
            raise ValueError("文件路径包含链接")
    return path


def transmit(sock, path):
    with path.open("rb") as stream:
        while block := stream.read(128 * 1024):
            sock.sendall(struct.pack("!I", len(block)) + block)
    sock.sendall(bytes(4))


def receive(sock, path, expected, old):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".lan-sync-", delete=False) as stream:
            tmp = Path(stream.name)
            hasher = hashlib.sha256()
            while size := struct.unpack("!I", exact(sock, 4))[0]:
                if size > 128 * 1024:
                    raise ValueError("数据块过大")
                block = exact(sock, size)
                stream.write(block)
                hasher.update(block)
        if hasher.hexdigest() != expected or (digest(path) if path.exists() else None) != old:
            raise ValueError("同步期间文件发生变化，请重新连接")
        os.replace(tmp, path)
    finally:
        if tmp:
            tmp.unlink(missing_ok=True)


def manifest(root):
    return {k: [p.as_posix(), h] for k, (p, h) in scan(root).items()}


def serve(sock, root, status):
    while True:
        cmd, *args = read(sock)
        if cmd == "list":
            send(sock, manifest(root))
        elif cmd == "get":
            transmit(sock, location(root, args[0]))
        elif cmd == "put":
            receive(sock, location(root, args[0]), args[1], args[2])
            send(sock, True)
        elif cmd == "status":
            status(str(args[0]))
        else:
            raise ValueError("无效请求")


def cycle(sock, root, state):
    left = manifest(root)
    send(sock, ["list"])
    right = read(sock)
    known = json.loads(state.read_text()) if state.exists() else {}
    conflicts = []
    for key in sorted(left.keys() | right.keys()):
        x, y = left.get(key), right.get(key)
        if x and y and x[1] == y[1]:
            known[key] = x[1]
        elif x and (not y or y[1] == known.get(key)):
            send(sock, ["put", (y or x)[0], x[1], y and y[1]])
            transmit(sock, location(root, x[0]))
            if read(sock) is not True:
                raise ValueError("对方未确认写入")
            known[key] = x[1]
        elif y and (not x or x[1] == known.get(key)):
            send(sock, ["get", y[0]])
            receive(sock, location(root, (x or y)[0]), y[1], x and x[1])
            known[key] = y[1]
        else:
            conflicts.append(key)
    tmp = state.with_suffix(".tmp")
    tmp.write_text(json.dumps({k: known[k] for k in left.keys() | right.keys() if k in known}))
    os.replace(tmp, state)
    return "需手动合并：" + "、".join(conflicts) if conflicts else "已同步 " + time.strftime("%H:%M:%S")
