# Notifier

A Frappe/ERPNext app for sending and managing WhatsApp messages.

It talks to a **[WuzAPI](https://github.com/asternic/wuzapi)** server — a REST
gateway built on the [`whatsmeow`](https://github.com/tulir/whatsmeow) Go library
(WhatsApp Web multi-device). WuzAPI replaces the previous Evolution API backend.

## Architecture

```
Frappe (this app, Python)  ──HTTP──▶  WuzAPI (Go, whatsmeow)  ──▶  WhatsApp
```

`whatsmeow` is a Go *library*, not a server, so it cannot be called from Python
directly. WuzAPI wraps it in a REST API that this app calls.

* `notifier/wuzapi.py` — low-level WuzAPI HTTP client.
* `notifier/api.py` — whitelisted send / instance / contact methods.
* `WhatsApp Instance` / `WhatsApp Message` controllers — lifecycle + sending.
* `notifier/webhook.py` — receives WuzAPI events (connection status).

## 1. Run WuzAPI

```bash
git clone https://github.com/asternic/wuzapi.git
cd wuzapi
# choose an admin token; the app uses it to create per-instance sessions
export WUZAPI_ADMIN_TOKEN="pick-a-strong-secret"
go build .
./wuzapi                       # listens on :8080 by default (SQLite/PostgreSQL)
```

Run it under systemd or Docker so it stays up next to your bench.

## 2. Configure the app

Open **WhatsApp Settings** (single doctype) and set:

| Field | Value |
|-------|-------|
| WuzAPI Base URL | `http://127.0.0.1:8080` (or your WuzAPI host) |
| WuzAPI Admin Token | the same value as `WUZAPI_ADMIN_TOKEN` |

## 3. Connect a WhatsApp number

1. Create a **WhatsApp Instance** (a random per-session token is generated and
   registered with WuzAPI automatically via `after_insert`).
2. Open it and click **Refresh QR Code**, then scan the QR with WhatsApp on your
   phone (Linked Devices).
3. On successful pairing WuzAPI posts a webhook back and the instance `status`
   flips to **Open**.

## 4. Send a message

Create a **WhatsApp Message** (choose the instance, recipient `to`, and either
text or an attachment). It is sent on insert.

## 5. Send a bill's PDF from the list or form ("Actions > Send WhatsApp")

1. In a list (e.g. Sales Invoice), tick one or more documents, or open one.
2. Click **Actions > Send WhatsApp**.
3. Choose the **WhatsApp Instance** and **Print Format** (both are remembered
   for next time), optionally edit the message, and click **Send**.

Each document's PDF is sent to its own customer / supplier number through that
instance - nothing opens in the browser. The number is taken from the document
(`contact_mobile`, `mobile_no`, any custom `*phone*`/`*mobile*` field), then the
contact person, then the customer / supplier and its contacts. 10-digit numbers
get the **Default Country Code** from WhatsApp Settings (91 by default). More
than 5 documents are sent in the background and the result pops up when done.
A comment is added on each document that was sent.

The button appears on printable doctypes that have a customer, supplier or
party. If the site has older Client Scripts adding a "Send WhatsApp" button
that opens `wa.me`, disable them.

## Auth model (important)

Unlike Evolution API (one global `apikey` + instance name in the URL), WuzAPI
authenticates **per session**:

* Normal endpoints use a `Token` header carrying the instance's own token
  (stored on `WhatsApp Instance.token`).
* Admin endpoints (`/admin/users`) use an `Authorization` header carrying the
  admin token (`WhatsApp Settings.api_token`).

## Notes & limitations

* **Media is sent as base64** — WuzAPI does not fetch remote URLs. Attachments
  are read and base64-encoded automatically.
* **Audio** should be Opus/OGG; other formats may be rejected by WhatsApp.
* **Interactive buttons / list / poll** messages are not implemented. WhatsApp
  restricts these on unofficial (web multi-device) clients like whatsmeow, so
  the old test stubs were removed.
* The settings doctype was renamed from *Evolution API Settings* to
  *WhatsApp Settings*. A migration patch preserves any previously saved values.

#### License

mit
