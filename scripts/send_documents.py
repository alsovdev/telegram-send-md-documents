#!/usr/bin/env python3
"""
Send one or more files as documents via Telegram Bot API.

Usage:
    python3 send_documents.py FILE1 [FILE2 ...]
    python3 send_documents.py --chat-id 12345 FILE1 FILE2

Reads TELEGRAM_BOT_TOKEN from /home/usr/.hermes/.env or TELEGRAM_BOT_TOKEN env var.
Default chat_id: 253742472 (Александр Соловьёв DM).

Each file is sent as a separate sendDocument request via multipart/form-data.
"""
import urllib.request, json, base64, os, sys, glob

def read_telegram_config():
    """Read token and chat_id from Hermes .env file."""
    env_path = os.path.expanduser('~/.hermes/.env')
    token = None
    chat_id = None
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if 'TELEGRAM_BOT_TOKEN' in line and not line.startswith('#'):
                    token = line.strip().split('=', 1)[1].strip()
                if 'TELEGRAM_HOME_CHANNEL' in line and not line.startswith('#'):
                    chat_id = line.strip().split('=', 1)[1].strip()
    # Fallbacks
    if not token:
        token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    if not chat_id:
        chat_id = '253742472'
    return token, chat_id

def send_document(token, chat_id, file_path, filename=None):
    """Send a single file as a document via Telegram Bot API."""
    if filename is None:
        filename = os.path.basename(file_path)
    
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    body = b''
    body += ('--' + boundary + '\r\n').encode()
    body += b'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
    body += (str(chat_id) + '\r\n').encode()
    body += ('--' + boundary + '\r\n').encode()
    body += ('Content-Disposition: form-data; name="document"; filename="' + filename + '"\r\n').encode()
    body += b'Content-Type: text/markdown\r\n\r\n'
    body += file_data + b'\r\n'
    body += ('--' + boundary + '--\r\n').encode()
    
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        return data

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Send files as Telegram documents')
    parser.add_argument('files', nargs='+', help='File paths to send')
    parser.add_argument('--chat-id', default='253742472', help='Target chat ID')
    parser.add_argument('--filename', '-n', help='Custom filename (single file only)')
    parser.add_argument('--content-type', '-c', default='text/markdown', help='Content-Type (default: text/markdown)')
    args = parser.parse_args()
    
    token, default_chat_id = read_telegram_config()
    if not token or len(token) < 30:
        print(f"ERROR: Invalid token (length={len(token)}). Check ~/.hermes/.env", file=sys.stderr)
        sys.exit(1)
    
    errors = []
    for fp in args.files:
        if not os.path.exists(fp):
            print(f"SKIP: {fp} not found")
            errors.append(fp)
            continue
        
        if os.path.isdir(fp):
            # Glob all .md files in directory
            matched = sorted(glob.glob(os.path.join(fp, '*.md')))
            if not matched:
                print(f"SKIP: no .md files in {fp}")
                continue
            for m in matched:
                try:
                    result = send_document(token, args.chat_id or default_chat_id, m)
                    fname = result.get('result', {}).get('document', {}).get('file_name', m)
                    print(f"OK: {m} -> {fname}")
                except urllib.error.HTTPError as e:
                    print(f"FAIL: {m} - HTTP {e.code}: {e.read().decode()[:200]}")
                    errors.append(m)
            continue
        
        try:
            fname = args.filename if args.filename else os.path.basename(fp)
            result = send_document(token, args.chat_id or default_chat_id, fp)
            sent_name = result.get('result', {}).get('document', {}).get('file_name', fname)
            print(f"OK: {fp} -> {sent_name}")
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"FAIL: {fp} - HTTP {e.code}: {body[:200]}", file=sys.stderr)
            errors.append(fp)
    
    if errors:
        print(f"\n{len(errors)} file(s) failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
