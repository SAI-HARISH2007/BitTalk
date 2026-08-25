# BitTalk — Classroom Chat & Admin System

A networked classroom chat system built on raw Python sockets: a multithreaded TCP server with a live admin console, and a desktop GUI client (CustomTkinter). No frameworks, no external chat libraries.

## What it does

- **Multithreaded server** — each client runs on its own thread; shared state is guarded with locks
- **Login/auth** — students sign in with an enrollment number, validated server-side (`student_data.py` stays on the server machine only; the copy in this repo is sample data)
- **Admin console** — the server terminal doubles as a moderation console (`/help` for commands): broadcast, kick, and monitor all messages centrally
- **GUI client** — dark-mode CustomTkinter app with login screen and live message feed

## Run it

```bash
pip install customtkinter

# on the host machine
python server.py          # listens on 0.0.0.0:12345

# on each student machine
python client.py          # point it at the server's IP
```

## Design notes

- Threads are daemonized so a dead client can't hang shutdown; `SO_REUSEADDR` allows quick restarts
- All messages are logged and echoed to the server console for moderation
- Auth data is intentionally server-side only — clients never see the student roster
