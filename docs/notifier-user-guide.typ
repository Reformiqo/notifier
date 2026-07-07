#set document(title: "Notifier — WhatsApp for ERPNext", author: "Reformiqo")
#set page(
  paper: "a4",
  margin: (x: 2cm, top: 2cm, bottom: 1.8cm),
  footer: context [
    #set text(size: 8pt, fill: gray)
    #line(length: 100%, stroke: 0.4pt + gray)
    #v(2pt)
    Notifier · WhatsApp for ERPNext
    #h(1fr)
    Page #counter(page).display() / #counter(page).final().first()
  ],
)
#set text(size: 10.5pt, lang: "en", fill: rgb("#1f2937"))
#set par(justify: true, leading: 0.62em)

#let accent = rgb("#128C7E")
#let green = rgb("#25D366")

#set heading(numbering: "1.1")
#show heading.where(level: 1): it => {
  set text(fill: white, weight: "bold", size: 14pt)
  v(0.5em)
  block(fill: accent, inset: (x: 10pt, y: 7pt), radius: 4pt, width: 100%, it)
  v(0.2em)
}
#show heading.where(level: 2): it => {
  set text(fill: accent, weight: "bold", size: 11.5pt)
  block(above: 1em, below: 0.5em, it)
}

#show raw.where(block: true): it => block(
  fill: rgb("#0f172a"), inset: 9pt, radius: 4pt, width: 100%,
  text(fill: rgb("#e2e8f0"), size: 8.5pt, it),
)
#show raw.where(block: false): it => box(
  fill: rgb("#eef2f7"), inset: (x: 3pt, y: 1pt), outset: (y: 2pt), radius: 2pt,
  text(fill: rgb("#0f172a"), it),
)

#let note(title, body) = block(
  fill: rgb("#f0fdf4"), stroke: (left: 3pt + green), inset: 10pt,
  radius: 2pt, width: 100%,
  [#text(weight: "bold", fill: accent)[#title] \ #body],
)
#let warn(title, body) = block(
  fill: rgb("#fff7ed"), stroke: (left: 3pt + rgb("#ea580c")), inset: 10pt,
  radius: 2pt, width: 100%,
  [#text(weight: "bold", fill: rgb("#ea580c"))[#title] \ #body],
)
#let step(n, body) = grid(
  columns: (1.1em, 1fr), gutter: 7pt,
  text(fill: green, weight: "bold")[#n.], body,
)

// ---- Title ----
#align(center)[
  #v(0.6cm)
  #text(size: 30pt, weight: "bold", fill: accent)[Notifier]
  #v(-0.35em)
  #text(size: 15pt)[WhatsApp for ERPNext — User Guide]
  #v(0.4em)
  #text(size: 9.5pt, fill: gray)[
    Send WhatsApp from ERPNext through WuzAPI (whatsmeow) · QR pairing · No per-message fees
  ]
]
#v(0.3cm)
#align(center)[
  #box(fill: rgb("#f8fafc"), stroke: 0.5pt + rgb("#cbd5e1"), inset: 9pt, radius: 4pt)[
    #text(size: 10pt)[
      *Frappe / ERPNext* #h(6pt) → #h(6pt) *WuzAPI* (whatsmeow) #h(6pt) → #h(6pt) *WhatsApp*
    ]
  ]
]
#v(0.4cm)

= Overview

Notifier connects your ERPNext site to WhatsApp. Instead of paying per message
through the official API, it drives *WuzAPI* — a self-hosted gateway built on the
`whatsmeow` library — which links to WhatsApp by scanning a QR code, exactly like
WhatsApp Web.

With it you can:

- Link one or more WhatsApp numbers ("instances") by scanning a QR code.
- Send messages manually to a *phone number* or a *group chat*.
- Broadcast templated messages to a contact group.
- Automatically send WhatsApp alerts on any ERPNext event using the standard
  *Notification* doctype (e.g. a Sales Invoice on submit), optionally with the
  document's PDF attached.

#note("Gateway", [The WuzAPI gateway for this deployment runs at
  `https://wuzapi.manage.reformiqo.in`. You normally never open it directly —
  ERPNext talks to it for you.])

= First-time setup

You only do this once per site.

== WhatsApp Settings

Search the awesomebar for *WhatsApp Settings* and fill in:

#table(
  columns: (auto, 1fr),
  stroke: 0.5pt + rgb("#cbd5e1"),
  inset: 7pt,
  fill: (_, row) => if row == 0 { rgb("#f1f5f9") },
  [*Field*], [*Value*],
  [WuzAPI Base URL], [`https://wuzapi.manage.reformiqo.in`],
  [WuzAPI Admin Token], [the gateway admin token (kept by your administrator)],
)

Save. That's the whole configuration — every instance you create is registered
with the gateway automatically.

= Connect a WhatsApp number

Each WhatsApp number you send from is a *WhatsApp Instance*.

#step(1)[Open *WhatsApp Instance* → *New*. Give it a *Label* (e.g. `khan`) and the
  *Phone Number* with country code (e.g. `2206084445`). Save.]
#step(2)[Click *Refresh QR Code*. A QR image appears on the form.]
#step(3)[On the phone, open *WhatsApp → Linked Devices → Link a Device* and scan
  the QR.]
#step(4)[Once paired, the status badge turns *Open* and the QR disappears.]

#note("Tip", [Status refreshes on its own every couple of minutes, and whenever
  you open the instance. You can also press *Check Connection* to refresh it
  instantly.])

== Check Connection & group sync

The *Check Connection* button does two things:

- Reads the live connection state from the gateway and updates the badge.
- If the number is connected, it *fetches every WhatsApp group* that number
  belongs to and saves them into the *WhatsApp Group* list.

Run it once after pairing so your groups are available to pick when sending.

= Send a message manually

Open *WhatsApp Message* → *New*.

#step(1)[Pick the *Instance* to send from.]
#step(2)[Choose *Send To*:
  #block(inset: (left: 1.1em, top: 3pt))[
    - *Phone* — type the number in *TO* (with country code).
    - *Group* — pick a *WhatsApp Group* (only that instance's groups are shown).
  ]
]
#step(3)[Set *Content Type* (`text`, `image`, `document`, `audio`, …). For media,
  use *Attach* to upload the file.]
#step(4)[Type the *Message* and Save — it sends on save.]

The *Message ID* field fills in once WhatsApp accepts it, and every message is
kept as a record (your communication log).

#warn("Media & audio", [Attachments are uploaded to WhatsApp as data, not links.
  Audio should be Opus/OGG; other formats may be rejected by WhatsApp.])

= Broadcasts

Use *WhatsApp Broadcast* to send a templated message to everyone in a contact
group:

#step(1)[Create a *WhatsApp Template* with your message. Use `{{ fieldname }}` to
  pull values from each contact (e.g. `Hi {{ first_name }}`).]
#step(2)[Create a *WhatsApp Broadcast* → choose the *Instance*, *Contact Group*
  and *Template* → *Submit*. Each recipient gets an individual message.]

= Automation — WhatsApp as a Notification channel

This is the powerful part: WhatsApp is now a *channel* on ERPNext's built-in
*Notification*, so you can trigger messages on any document event with conditions
and Jinja — no coding.

#step(1)[Open *Notification* → *New*. Set *Channel* = *WhatsApp*.]
#step(2)[Pick the *WhatsApp Instance* to send from.]
#step(3)[Choose *Send To*:
  #block(inset: (left: 1.1em, top: 3pt))[
    - *Phone* — set *Recipient Phone Field* to the docfield holding the number
      (e.g. `contact_mobile`), or add a *Recipients* row → "Receiver By Document
      Field".
    - *Group* — pick a *WhatsApp Group*.
  ]
]
#step(4)[Under *Filters*, set *Document Type* (e.g. `Sales Invoice`), *Send Alert
  On* (e.g. `Submit`), and an optional *Condition*.]
#step(5)[Write the *Message* body. Jinja works: #box[`{{ doc.customer_name }}`],
  #box[`{{ doc.grand_total }}`], etc.]
#step(6)[Optional: tick *Attach Print* and pick a *Print Format* to also send the
  document's PDF.]

*Example* — WhatsApp the customer when an invoice is submitted:

#table(
  columns: (auto, 1fr),
  stroke: 0.5pt + rgb("#cbd5e1"),
  inset: 7pt,
  fill: (_, row) => if row == 0 { rgb("#f1f5f9") },
  [*Setting*], [*Value*],
  [Channel], [WhatsApp],
  [WhatsApp Instance], [`khan`],
  [Send To], [Phone],
  [Recipient Phone Field], [`contact_mobile`],
  [Document Type], [Sales Invoice],
  [Send Alert On], [Submit],
  [Message], [`Hi {{ doc.customer_name }}, invoice {{ doc.name }} for {{ doc.grand_total }} is ready.`],
  [Attach Print], [☑ (Standard print format)],
)

= Reference

== Instance status

#table(
  columns: (auto, 1fr),
  stroke: 0.5pt + rgb("#cbd5e1"),
  inset: 7pt,
  fill: (_, row) => if row == 0 { rgb("#f1f5f9") },
  [*Badge*], [*Meaning*],
  [*Open*], [Connected and logged in — ready to send.],
  [*Connecting*], [Session started, waiting for you to scan the QR.],
  [*Closed*], [Not connected / logged out — press *Refresh QR Code* and scan again.],
)

== Troubleshooting

#table(
  columns: (1fr, 1.3fr),
  stroke: 0.5pt + rgb("#cbd5e1"),
  inset: 7pt,
  fill: (_, row) => if row == 0 { rgb("#f1f5f9") },
  [*Symptom*], [*Fix*],
  [Status stuck on *Connecting* after scanning], [Press *Check Connection*. It reads the true state from the gateway.],
  [Group dropdown is empty], [Run *Check Connection* on the instance first to sync groups.],
  [Message sent but recipient got nothing], [Confirm the number is a real WhatsApp account and includes the country code.],
  [Instance went *Closed* on its own], [The phone unlinked the device or lost the session — re-scan the QR.],
)
