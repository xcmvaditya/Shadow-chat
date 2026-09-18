# ShadowChat

**Developed by Aditya**

A terminal-based encrypted chat tool built for Termux. Connects to Firebase Realtime Database, encrypts every message with AES-256, and runs entirely from the command line.

---

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Firebase Setup](#firebase-setup)
5. [Running ShadowChat](#running-shadowchat)
6. [Commands](#commands)
7. [Example Session](#example-session)
8. [Project Structure](#project-structure)
9. [Troubleshooting](#troubleshooting)
10. [Security Notes](#security-notes)
11. [License](#license)
12. [Author](#author)

---

## Features

- AES-256 encrypted messages (Fernet, per-room key derivation)
- Multi-user register / login (SHA-256 hashed passwords)
- Multi-room support with `/join` and `/leave`
- Direct messages via `/dm <user> <msg>`
- File transfer over chat (base64, files under 1 MB)
- Real-time incoming message stream
- Session resume across app restarts
- Hacker-green terminal UI built with `rich`

---

## Requirements

- Termux (F-Droid version recommended)
- Android 7.0 or higher
- Internet connection
- A Firebase project with Realtime Database enabled

---

## Installation

Copy and paste these commands one by one in Termux:

```bash
pkg update -y && pkg upgrade -y
pkg install -y git python
git clone https://github.com/xcmvaditya/Shadow-chat.git
cd Shadow-chat
bash install.sh
```

The `install.sh` script will install all remaining dependencies (`cmake`, `libffi`, `openssl`, `termux-api`) and the Python packages listed in `requirements.txt`.

After install completes, verify the files:

```bash
ls
```

You should see:

```
LICENSE    firebase_config.json  requirements.txt
README.md  install.sh            shadowchat.py
```

---

## Firebase Setup

Before running the app, edit `firebase_config.json` in the project folder with your own Firebase details:

```json
{
  "databaseURL": "https://your-project-default-rtdb.firebaseio.com",
  "apiKey": "YOUR_API_KEY",
  "projectId": "your-project-id"
}
```

To get these values:

1. Go to https://console.firebase.google.com
2. Create a new project (or open an existing one)
3. Left sidebar → **Build** → **Realtime Database** → **Create Database**
4. Choose **Start in test mode** (for development)
5. Go to **Project Settings** (gear icon) → **General** → scroll down to **Your apps**
6. Copy the `databaseURL`, `apiKey`, and `projectId` into `firebase_config.json`

Edit the file directly in Termux with nano:

```bash
nano firebase_config.json
```

Save with `Ctrl+O`, `Enter`, then exit with `Ctrl+X`.

> **Note:** Test mode rules allow anyone with the URL to read/write. For personal use this is fine. Before sharing the URL publicly, lock the rules down from the Realtime Database → Rules tab.

---

## Running ShadowChat

```bash
python shadowchat.py
```

On first launch you'll see:

```
1  Login
2  Register
3  Exit
```

- Pick **2** to create a new account (username + password)
- Enter a room name (default is `general`)
- Start typing to chat

Your session is saved in `.session`, so next time you can skip login.

To stop ShadowChat at any time, type `/exit` inside the chat or press `Ctrl+C`.

---

## Commands

Type these inside the chat window (they start with a forward slash):

| Command | What it does |
|---|---|
| `/help` | Show all available commands |
| `/users` | List users in the current room |
| `/rooms` | List every room and its member count |
| `/join <room>` | Switch to another room |
| `/leave` | Leave the current room |
| `/dm <user> <msg>` | Send a direct message to another user |
| `/send <file>` | Send a file to the current room |
| `/clear` | Clear the local message buffer |
| `/exit` | Quit ShadowChat |

Anything that does **not** start with `/` is sent as a normal message to the current room.

---

## Example Session

```bash
$ python shadowchat.py

# On first run:
select: 2
username: aditya
password: ****
room: general

# Inside the chat:
> hey everyone
> /users
> /join hacking
> /dm rahul check this out
> /send /sdcard/notes.txt
> /exit
```

---

## Project Structure

```
Shadow-chat/
├── shadowchat.py            # Main application
├── firebase_config.json     # Your Firebase credentials
├── requirements.txt         # Python dependencies
├── install.sh               # One-shot installer for Termux
├── README.md                # This file
└── LICENSE                  # MIT
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'rich'`

Run the install step again inside the project folder:

```bash
pip install -r requirements.txt
```

### `firebase_config.json missing`

Make sure you are running the app from inside the `Shadow-chat/` directory:

```bash
cd ~/Shadow-chat
python shadowchat.py
```

### Messages not showing up for other users

Double-check that all users are in the same room, and that the `databaseURL` in `firebase_config.json` is correct.

### `requests.exceptions.HTTPError: 401` or `403`

Firebase Realtime Database rules are blocking writes. Set them to test mode. Go to Firebase Console → Realtime Database → Rules, paste this, and click Publish:

```json
{
  "rules": {
    ".read": true,
    ".write": true
  }
}
```

### Session stuck on "invalid credentials"

Delete the `.session` file and restart:

```bash
rm .session
python shadowchat.py
```

### `command not found: python`

Install Python in Termux:

```bash
pkg install python -y
```

### Permission denied on `install.sh`

Make it executable, then run:

```bash
chmod +x install.sh
bash install.sh
```

### `pip: command not found`

Reinstall Python:

```bash
pkg install python -y
```

---

## Security Notes

- Passwords are hashed with SHA-256 before being stored
- Messages are encrypted with Fernet (AES-128 in CBC mode with HMAC) using a key derived from `username:room` via SHA-256
- Both users in a DM derive the same key, so DMs are readable by both parties only
- The Firebase `apiKey` in `firebase_config.json` is safe to expose — it is a client identifier, not a secret
- Never commit a `serviceAccountKey.json` to the repo — it grants admin access to your Firebase project
- The `.gitignore` file already blocks `.session` and `serviceAccountKey.json` from being committed

---

## License

MIT — see `LICENSE` for the full text.

---

## Author

**Aditya**

- GitHub: [@xcmvaditya](https://github.com/xcmvaditya)
- Project: [Shadow-chat](https://github.com/xcmvaditya/Shadow-chat)

Built for the shadows. Stay encrypted.
