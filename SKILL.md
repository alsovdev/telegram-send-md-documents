---
name: telegram-send-md-documents
description: "Send Markdown documents (.md files) to Telegram chat as actual document attachments (not text messages). Use when user asks to send/present MD files to Telegram."
platforms: [linux, macos, windows]
---

# Send MD Documents to Telegram

## When to use

When the user asks to send, deliver, or present Markdown (.md) files to a Telegram chat. The built-in `send_message` tool with `MEDIA:` parameter does NOT send files as documents — it auto-detects them as photo/video/audio and renders them inline. This skill uses direct Telegram Bot API to send actual downloadable document files.

## Prerequisites

- Telegram Bot Token stored in `/home/usr/.hermes/.env` as `TELEGRAM_BOT_TOKEN`
- Bot already connected via Hermes gateway
- Target chat ID known (default: `253742472` for user's DM)

## Method: curl multipart POST to sendDocument

Use Python script to send file as document via Telegram Bot API:

```python
import urllib.request, json

# Read token
token = None
with open('/home/usr/.hermes/.env') as f:
    for line in f:
        if 'TELEGRAM_BOT_TOKEN' in line and not line.startswith('#'):
            token = line.strip().split('=', 1)[1].strip()
            break

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
file_path = '/path/to/file.md'  # Replace with actual path
filename = 'document.md'          # Replace with desired filename (Russian OK)
chat_id = '253742472'             # Replace if different

with open(file_path, 'rb') as f:
    file_data = f.read()

body = b''
body += ('--' + boundary + '\r\n').encode()
body += b'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
body += (chat_id + '\r\n').encode()
body += ('--' + boundary + '\r\n').encode()
body += ('Content-Disposition: form-data; name="document"; filename="' + filename + '"\r\n').encode()
body += b'Content-Type: text/markdown\r\n\r\n'
body += file_data + b'\r\n'
body += ('--' + boundary + '--\r\n').encode()

url = f"https://api.telegram.org/bot{token}/sendDocument"
req = urllib.request.Request(url, data=body, method='POST')
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    if data.get('ok'):
        print(f"OK: {filename} sent as document")
    else:
        print(f"FAIL: {data}")
```

### Sending multiple files

Loop over files with same boundary:

```python
files = [
    ('/path/to/file1.md', 'документ1.md'),
    ('/path/to/file2.md', 'документ2.md'),
    ('/path/to/file3.md', 'документ3.md'),
]

for file_path, filename in files:
    # ... same body construction per file ...
    # Send each file in a separate request
```

## Key details

- **Content-Type**: `text/markdown` (not `text/plain`)
- **Filename**: Can be in Cyrillic, with spaces, must end in `.md`
- **File size limit**: Telegram Bot API limit is 2 GB for documents
- **Token location**: `/home/usr/.hermes/.env` → `TELEGRAM_BOT_TOKEN=...`
- **chat_id**: `253742472` (Александр Соловьёв DM)

## Why not `send_message` with `MEDIA:`?

`send_message` with `MEDIA:/path` auto-detects file type:
- Images → renders as photo
- Videos → renders as video
- Audio → renders as voice message
- Everything else → may render as text or fail

It does NOT send as a downloadable document with `sendDocument` endpoint. The curl multipart method is required for proper document delivery.

## Reusable script

`scripts/send_documents.py` — handles token reading, multipart construction, and batch sending. Run directly:

```bash
python3 ~/.hermes/skills/productivity/telegram-send-md-documents/scripts/send_documents.py file1.md file2.md
# With custom chat:
python3 .../send_documents.py --chat-id 12345 file.md
# Send whole directory of .md files:
python3 .../send_documents.py ./notes/
```

## Related

- `references/github-upload-via-api.md` — same pattern for pushing code/artifacts to GitHub via API when `gh` CLI is unavailable.

## Pitfalls

1. **Token masked in logs**: The token may appear as `***` in terminal output. Use Python to read it programmatically.
2. **Token truncated in heredoc/echo**: When passing tokens via bash heredoc or echo, special characters or length may cause truncation. Always write tokens to a file first (`/tmp/token.txt`) then read in Python, or pass as script argument.
3. **Bytes + string mixing**: In the multipart body, use `.encode()` for string parts and `b''` for binary parts.
4. **Filename encoding**: Cyrillic filenames work fine in the `Content-Disposition` header.
5. **One request per file**: Don't batch multiple files in one multipart request — send each separately.
6. **`send_message` MEDIA: does NOT work for documents**: The built-in `send_message` tool auto-detects file types and renders as photo/video/audio. It cannot send arbitrary files as downloadable documents. Always use this skill's method for document delivery.
