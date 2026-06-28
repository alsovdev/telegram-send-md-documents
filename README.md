# telegram-send-md-documents

Skill for sending Markdown documents as actual file attachments via Telegram Bot API.

## Problem

The built-in send_message tool with MEDIA: parameter does NOT send files as documents. Telegram auto-detects them as photo/video/audio and renders them inline.

## Solution

Use direct Telegram Bot API sendDocument endpoint via multipart POST.

## Files

- SKILL.md — Full skill documentation with Python script for sending MD files

## Usage

When user asks to send MD files to Telegram, use the method from SKILL.md.
