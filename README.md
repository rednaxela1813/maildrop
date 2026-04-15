# Maildrop

`maildrop` is a local CLI utility that connects to an IMAP mailbox, fetches unseen emails with attachments, routes supported files into a structured directory (e.g. Nextcloud), and maintains a local SQLite state to ensure safe, repeatable processing.

The current implementation is a command-line tool, not a daemon or background service.

---

## Why this exists

Managing documents from email manually is error-prone and time-consuming.

Maildrop automates:

- collecting documents from email
- sorting them into structured folders
- preparing them for accounting or further processing

---

## What it does

On `maildrop scan`, the tool:

1. Loads settings from environment variables or `.env`
2. Connects to IMAP over SSL
3. Fetches `UNSEEN` messages from the configured mailbox
4. Extracts and normalizes file attachments
5. Filters attachments by globally allowed extensions
6. Matches each attachment against YAML routing rules
7. Saves files into a structured destination directory
8. Records processed messages and attachments in SQLite

Saved files follow this naming pattern:

```text
YYYY-MM-DD_original_filename.ext

Example:

2026-03-02_INV_23201092_2304007430.CSV
Deduplication model

Deduplication is local and based on SQLite state:

messages are tracked by IMAP source_id
attachments are deduplicated by (checksum, destination_path)

This allows:

safe re-running of scans
prevention of duplicate file writes
keeping IMAP mailbox unchanged
Idempotency

The scan operation is idempotent:

running maildrop scan multiple times does not duplicate files
already processed messages and attachments are skipped
Current behavior and limitations
Only messages returned by IMAP UNSEEN are processed

⚠️ Important:

If a message is marked as SEEN by another client, it will not be processed by maildrop.

Message bodies are fetched using BODY.PEEK[], so maildrop does not intentionally mark messages as seen
The tool does not move messages between folders
The tool does not modify message state on the mail server
Deduplication is local only (SQLite)
Message identification

Messages are tracked using IMAP source_id.

⚠️ Important:

The source_id depends on the IMAP server implementation and may not be globally stable.
The tool assumes identifiers remain consistent within the mailbox.

Attachment handling behavior
Only allowed extensions are processed
Unsupported attachments are skipped
Skipped attachments still mark the message as "handled"

This prevents repeated reprocessing of messages containing only unsupported files.

Failure scenarios
If IMAP connection fails → scan stops, no partial state written
If saving a file fails → attachment is not recorded as delivered
Messages are marked as processed only after at least one attachment was handled
Concurrency

The tool is designed for single-process usage.

Running multiple scans in parallel may lead to race conditions in SQLite state.

Requirements
Python >=3.12
IMAP account access
Local directory (e.g. Nextcloud mount)
Installation

From the project/ directory:

python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
Usage
Show available commands
maildrop --help
Debug IMAP (safe mode)
maildrop debug-imap
Lists unseen messages and attachments
Does not modify message state
Does not save files
Dry run
maildrop scan --dry-run
Shows what would be saved
Does not write files
Does not update SQLite state
Run scan
maildrop scan

Performs full processing:

fetches unseen messages
routes attachments
writes files
updates local state
Configuration

Create .env in project root:

IMAP_HOST=imap.example.com
IMAP_PORT=993
IMAP_USER=user@example.com
IMAP_PASSWORD=app-password
IMAP_MAILBOX=INBOX

NEXTCLOUD_MOUNT_PATH=/absolute/path/to/Nextcloud

SQLITE_PATH=./maildrop.db
RULES_FILE=./rules.yaml

LOG_LEVEL=INFO
ALLOWED_EXTENSIONS=.pdf,.csv,.xml
Routing rules

Rules are defined in rules.yaml.

Each rule includes:

name
priority (lower = higher priority)
enabled
sender_contains
subject_contains
filename_contains
allowed_extensions (optional)
destination

First matching rule wins.

Placeholders

Supported:

{yyyy}
{mm}
{dd}
Example
rules:
  - name: invoices_pdf
    priority: 10
    enabled: true
    sender_contains:
      - "billing@example.com"
    subject_contains:
      - "invoice"
    allowed_extensions:
      - ".pdf"
    destination: "Mail/Documents/Invoices/{yyyy}/{mm}"

fallback:
  destination: "Mail/Unsorted/{yyyy}/{mm}"
Output structure
<NEXTCLOUD_MOUNT_PATH>/<destination>/YYYY-MM-DD_filename.ext

Example:

/Nextcloud/Mail/Documents/Metro/2026/03/2026-03-02_INV_23201092_2304007430.CSV
Local state (SQLite)

Tables:

processed_messages
delivered_attachments

Used for:

deduplication
idempotent processing
Development

Run tests:

python -m pytest

Lint:

ruff check .
Project structure
project/
├── pyproject.toml
├── rules.yaml
├── README.md
├── src/maildrop/
│   ├── cli.py
│   ├── config.py
│   ├── imap_client.py
│   ├── rules.py
│   ├── scanner.py
│   ├── state.py
│   └── storage.py
└── tests/
Future improvements
IMAP UID-based tracking instead of message IDs
marking messages as seen or moving to folders
daemon / scheduled execution
integration with ERP / accounting systems
structured logging
License

MIT