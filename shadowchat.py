#!/usr/bin/env python3
# ShadowChat - Termux terminal chat
# Developed by Aditya

import os, sys, json, time, base64, hashlib, threading, queue
from datetime import datetime
from pathlib import Path
import requests
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich import box
from cryptography.fernet import Fernet

ROOT = Path(__file__).parent
CFG_FILE = ROOT / "firebase_config.json"
SESSION_FILE = ROOT / ".session"

if not CFG_FILE.exists():
    print("[!] firebase_config.json missing")
    sys.exit(1)

CFG = json.loads(CFG_FILE.read_text())
DB_URL = CFG["databaseURL"].rstrip("/")
console = Console()

BANNER = r"""
[bold green]
  ███████╗██╗  ██╗ █████╗ ██████╗  ██████╗ ██╗    ██╗
  ██╔════╝██║  ██║██╔══██╗██╔══██╗██╔═══██╗██║    ██║
  ███████╗███████║███████║██║  ██║██║   ██║██║ █╗ ██║
  ╚════██║██╔══██║██╔══██║██║  ██║██║   ██║██║███╗██║
  ███████║██║  ██║██║  ██║██████╔╝╚██████╔╝╚███╔███╔╝
  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝  ╚══╝╚══╝
[/bold green]
[bold yellow]         Developed by Aditya  -  Termux Build[/bold yellow]
"""

def derive_key(user, room):
    h = hashlib.sha256(f"{user}:{room}".encode()).digest()
    return base64.urlsafe_b64encode(h)

def encrypt(t, k): return Fernet(k).encrypt(t.encode()).decode()

def decrypt(t, k):
    try: return Fernet(k).decrypt(t.encode()).decode()
    except: return "[decrypt failed]"

class FB:
    def __init__(self, base): self.base = base
    def _u(self, p): return f"{self.base}/{p.strip('/')}.json"
    def get(self, p):
        r = requests.get(self._u(p), timeout=10); r.raise_for_status(); return r.json()
    def put(self, p, d):
        r = requests.put(self._u(p), json=d, timeout=10); r.raise_for_status(); return r.json()
    def post(self, p, d):
        r = requests.post(self._u(p), json=d, timeout=10); r.raise_for_status(); return r.json()
    def patch(self, p, d):
        r = requests.patch(self._u(p), json=d, timeout=10); r.raise_for_status(); return r.json()
    def delete(self, p):
        r = requests.delete(self._u(p), timeout=10); r.raise_for_status(); return r.json()

db = FB(DB_URL)

def save_session(u, r): SESSION_FILE.write_text(json.dumps({"username": u, "room": r}))
def load_session():
    if SESSION_FILE.exists():
        try: return json.loads(SESSION_FILE.read_text())
        except: return None
def clear_session():
    if SESSION_FILE.exists(): SESSION_FILE.unlink()

def get_user(u): return db.get(f"shadowchat/users/{u}")

def create_user(u, p):
    if get_user(u): return False
    db.put(f"shadowchat/users/{u}", {
        "username": u,
        "password": hashlib.sha256(p.encode()).hexdigest(),
        "created": int(time.time()*1000),
        "last_seen": int(time.time()*1000)
    })
    return True

def verify_user(u, p):
    d = get_user(u)
    if not d: return False
    return d["password"] == hashlib.sha256(p.encode()).hexdigest()

def touch_user(u): db.patch(f"shadowchat/users/{u}", {"last_seen": int(time.time()*1000)})

def send_message(room, sender, cipher):
    db.post(f"shadowchat/rooms/{room}/messages", {
        "sender": sender, "body": cipher, "ts": int(time.time()*1000)
    })

def fetch_messages(room):
    d = db.get(f"shadowchat/rooms/{room}/messages") or {}
    m = [{"id": k, **v} for k, v in d.items()]
    m.sort(key=lambda x: x.get("ts", 0))
    return m

def room_users(room):
    d = db.get(f"shadowchat/rooms/{room}/members") or {}
    return list(d.keys())

def join_room(room, user):
    db.put(f"shadowchat/rooms/{room}/members/{user}", True)
    db.put(f"shadowchat/rooms/{room}/meta", {"name": room, "created": int(time.time()*1000)})

def leave_room(room, user): db.delete(f"shadowchat/rooms/{room}/members/{user}")

def list_rooms():
    d = db.get("shadowchat/rooms") or {}
    return list(d.keys())

class ChatUI:
    def __init__(self, u, r):
        self.username = u
        self.room = r
        self.key = derive_key(u, r)
        self.messages = []
        self.running = True
        self.status = "online"

    def compose(self):
        header = Panel(Align.center(Text.assemble(
            ("SHADOWCHAT", "bold green"), (" | ", "dim"),
            ("user:", "dim"), (self.username, "bold cyan"), (" | ", "dim"),
            ("room:", "dim"), (self.room, "bold magenta"), (" | ", "dim"),
            (self.status, "bold green")
        )), border_style="green", box=box.ROUNDED)

        if not self.messages:
            body = Panel(Align.center("[dim]No messages yet.[/dim]"),
                         border_style="dim", box=box.ROUNDED, height=20)
        else:
            lines = []
            for m in self.messages[-200:]:
                ts = datetime.fromtimestamp(m["ts"]/1000).strftime("%H:%M")
                mine = m["sender"] == self.username
                st = "bold cyan" if mine else "bold magenta"
                txt = decrypt(m.get("body", ""), self.key)
                if txt.startswith("[FILE:"):
                    head = txt.split("\n", 1)[0]
                    txt = f"[dim]{head}[/dim]"
                lines.append(Text.assemble(
                    (f"[{ts}] ", "dim"), (m["sender"], st),
                    (" > ", "dim"), (txt, "white" if mine else "green")
                ))
            body = Panel(Text("\n").join(lines), border_style="dim",
                         box=box.ROUNDED, height=22, title="[dim]messages[/dim]")

        footer = Panel(Align.center(
            "[dim]/help /users /rooms /join /dm /send /exit[/dim]"
        ), border_style="green", box=box.ROUNDED)
        return Group(header, body, footer)

    def poll(self):
        while self.running:
            try:
                m = fetch_messages(self.room)
                if m: self.messages = m
                touch_user(self.username)
            except: pass
            time.sleep(2)

    def handle_command(self, line):
        p = line.strip().split(maxsplit=1)
        cmd = p[0].lower()
        arg = p[1] if len(p) > 1 else ""

        if cmd in ("/exit", "/quit"):
            leave_room(self.room, self.username)
            self.running = False
            return True
        elif cmd == "/help":
            console.print(Panel(
                "/help /users /rooms /join <room> /leave /dm <user> <msg> /send <file> /clear /exit",
                title="help", border_style="green"))
        elif cmd == "/users":
            us = room_users(self.room) or [self.username]
            t = Table(title=f"Users in {self.room}", box=box.SIMPLE)
            t.add_column("username", style="cyan")
            for u in us: t.add_row(u)
            console.print(t)
        elif cmd == "/rooms":
            rs = list_rooms()
            t = Table(title="Rooms", box=box.SIMPLE)
            t.add_column("room", style="magenta")
            t.add_column("members", style="cyan")
            for r in rs: t.add_row(r, str(len(room_users(r) or {})))
            console.print(t)
        elif cmd == "/join":
            if not arg: console.print("[red]usage: /join <room>[/red]")
            else:
                leave_room(self.room, self.username)
                self.room = arg
                self.key = derive_key(self.username, self.room)
                join_room(self.room, self.username)
                self.messages = []
        elif cmd == "/leave":
            leave_room(self.room, self.username)
        elif cmd == "/clear":
            self.messages = []
        elif cmd == "/dm":
            c = arg.split(maxsplit=1)
            if len(c) < 2: console.print("[red]usage: /dm <user> <msg>[/red]")
            else:
                target, msg = c
                dm = "dm-" + "_".join(sorted([self.username, target]))
                join_room(dm, self.username)
                join_room(dm, target)
                send_message(dm, self.username, encrypt(msg, derive_key(self.username, dm)))
                console.print(f"[green]to {target}: {msg}[/green]")
        elif cmd == "/send":
            if not arg or not os.path.isfile(arg):
                console.print("[red]usage: /send <file>[/red]")
            else:
                try:
                    with open(arg, "rb") as f: raw = f.read()
                    payload = f"[FILE:{os.path.basename(arg)}|{len(raw)}b]\n" + base64.b64encode(raw).decode()
                    send_message(self.room, self.username, encrypt(payload, self.key))
                    console.print(f"[green]sent {os.path.basename(arg)}[/green]")
                except Exception as e:
                    console.print(f"[red]fail: {e}[/red]")
        else: return False
        return True

def boot():
    console.clear()
    console.print(BANNER)

def login_flow():
    console.print(Panel(
        "[green]1[/green] Login\n[green]2[/green] Register\n[green]3[/green] Exit",
        title="ShadowChat auth", border_style="green"))
    choice = Prompt.ask("select", choices=["1","2","3"], default="1")
    if choice == "3": sys.exit(0)
    u = Prompt.ask("username").strip()
    p = Prompt.ask("password", password=True)
    if choice == "2":
        if not create_user(u, p):
            console.print("[red]exists[/red]"); return None
    else:
        if not verify_user(u, p):
            console.print("[red]bad creds[/red]"); return None
    r = Prompt.ask("room", default="general").strip() or "general"
    join_room(r, u)
    return u, r

_input_q = queue.Queue()

def _input_thread():
    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            _input_q.put(line.rstrip("\n"))
        except: break

threading.Thread(target=_input_thread, daemon=True).start()

def input_nb():
    try: return _input_q.get_nowait()
    except queue.Empty: return None

def main():
    boot()
    sess = load_session()
    u = r = None
    if sess:
        console.print(f"[dim]resume {sess['username']} @ {sess['room']}?[/dim]")
        if Confirm.ask("continue", default=True):
            u, r = sess["username"], sess["room"]
            join_room(r, u)
    if not u:
        res = login_flow()
        if not res: return main()
        u, r = res
    save_session(u, r)
    touch_user(u)

    ui = ChatUI(u, r)
    ui.messages = fetch_messages(r)
    threading.Thread(target=ui.poll, daemon=True).start()

    console.clear()
    console.print(BANNER)

    try:
        with Live(ui.compose(), refresh_per_second=2, console=console, screen=True) as live:
            while ui.running:
                live.update(ui.compose())
                line = input_nb()
                if line is None:
                    time.sleep(0.2); continue
                line = line.strip()
                if not line: continue
                if line.startswith("/"): ui.handle_command(line)
                else: send_message(ui.room, ui.username, encrypt(line, ui.key))
    except KeyboardInterrupt:
        ui.running = False
    finally:
        leave_room(r, u)
        console.print("[green]bye[/green]")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt:
        clear_session()
