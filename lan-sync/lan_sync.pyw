import hashlib
import json
import os
import queue
import secrets
import socket
import threading
import time
from pathlib import Path
from tkinter import Button, Label, Listbox, Tk, filedialog, messagebox

import peer


def main():
    win = Tk()
    win.withdraw()
    folder = filedialog.askdirectory(title="选择这台电脑要同步的文件夹", mustexist=True)
    if not folder:
        return
    root = Path(folder).resolve()
    store = Path.home() / ".lan-sync-state"
    if root == store or root in store.parents or store in root.parents:
        raise ValueError("请选择单独的同步文件夹")
    store.mkdir(exist_ok=True)
    identity = store / "device"
    if not identity.exists():
        identity.write_text(secrets.token_hex(16))
    folder_id = hashlib.sha256((identity.read_text() + str(root)).encode()).hexdigest()
    instance = secrets.token_hex(8)
    hostname = socket.gethostname()
    server = peer.tls_server()
    listener = socket.socket()
    listener.bind(("", 0))
    listener.listen(5)
    port = listener.getsockname()[1]
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp.bind(("", peer.PORT))
    udp.settimeout(1)
    events = queue.Queue()
    busy = threading.Lock()
    devices = {}
    rows = []
    status = Label(win, text="正在发现附近设备…", wraplength=500)
    win.title("局域网文件同步 · " + hostname)
    Label(win, text=f"本机目录：{root}", wraplength=500).pack(padx=16, pady=8)
    box = Listbox(win, width=58, height=7, exportselection=False)
    box.pack(padx=16)
    win.deiconify()

    def run(fn, *args):
        threading.Thread(target=fn, args=args, daemon=True).start()

    def announce():
        data = json.dumps([peer.MAGIC, instance, hostname, port]).encode()
        while True:
            try:
                udp.sendto(data, ("255.255.255.255", peer.PORT))
            except OSError as exc:
                events.put(("status", str(exc)))
            time.sleep(3)

    def discover():
        while True:
            try:
                data, (ip, _) = udp.recvfrom(2048)
                magic, ident, name, remote_port = json.loads(data)
                if (magic == peer.MAGIC and isinstance(ident, str) and ident != instance
                        and isinstance(name, str) and type(remote_port) is int and 0 < remote_port < 65536):
                    events.put(("device", (ident, name[:80], ip, remote_port)))
            except (ValueError, TypeError, OSError):
                continue

    def session(raw, address, outbound):
        try:
            with raw:
                raw.settimeout(90)
                if outbound:
                    raw.connect(address)
                ctx = peer.tls_client() if outbound else server
                with ctx.wrap_socket(raw, server_side=not outbound) as sock:
                    peer.send(sock, [hostname, folder_id])
                    name, remote = peer.read(sock)
                    binding = sock.get_channel_binding()
                    if not binding:
                        raise ValueError("无法生成连接校验码")
                    code = hashlib.sha256(binding).hexdigest()[:12].upper()
                    if outbound:
                        events.put(("status", f"等待 {name} 同意，请核对两台机器的校验码：{code}"))
                        approved = peer.read(sock)
                    else:
                        answer = queue.Queue(1)
                        events.put(("ask", (answer, f"{name}（{address[0]}）申请双向同步。\n本机目录：{root}\n请与对方屏幕核对校验码：{code}\n同意建立连接？")))
                        approved = answer.get(timeout=75)
                        peer.send(sock, approved)
                    if approved is not True:
                        events.put(("status", "连接申请已拒绝"))
                        return
                    events.put(("status", f"已连接 {name}，正在同步…"))
                    sock.settimeout(None)
                    if outbound:
                        state = store / (hashlib.sha256((folder_id + remote).encode()).hexdigest() + ".json")
                        while True:
                            msg = peer.cycle(sock, root, state)
                            peer.send(sock, ["status", msg])
                            events.put(("status", msg))
                            time.sleep(10)
                    else:
                        peer.serve(sock, root, lambda msg: events.put(("status", msg)))
        except Exception as exc:
            events.put(("status", "连接已结束：" + (str(exc) or "申请超时")))
        finally:
            busy.release()

    def accept():
        while True:
            raw, addr = listener.accept()
            if busy.acquire(False):
                run(session, raw, addr, False)
            else:
                raw.close()

    def connect():
        selected = box.curselection()
        if selected and busy.acquire(False):
            _, ip, p, _ = devices[rows[selected[0]]]
            status.config(text="正在发起连接申请…")
            run(session, socket.socket(), (ip, p), True)

    def refresh():
        while not events.empty():
            kind, data = events.get_nowait()
            if kind == "ask":
                answer, prompt = data
                answer.put(messagebox.askyesno("局域网连接申请", prompt, parent=win))
            elif kind == "device":
                ident, name, ip, p = data
                devices[ident] = (name, ip, p, time.monotonic())
            else:
                status.config(text=data)
        online = sorted(k for k, v in devices.items() if time.monotonic() - v[3] < 12)
        if rows != online:
            rows[:] = online
            box.delete(0, "end")
            for ident in rows:
                name, ip, _, _ = devices[ident]
                box.insert("end", f"{name}   {ip}")
        win.after(200, refresh)

    Button(win, text="向选中设备申请连接", command=connect).pack(pady=8)
    status.pack(padx=16, pady=8)
    Button(win, text="断开并退出", command=win.destroy).pack(pady=6)
    for fn in (announce, discover, accept):
        run(fn)
    refresh()
    win.mainloop()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        messagebox.showerror("无法启动", str(exc))
