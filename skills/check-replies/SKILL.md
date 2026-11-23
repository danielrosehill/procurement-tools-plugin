---
name: check-replies
description: Check WhatsApp, email and voicemail for seller replies, answer questions, send a photo when asked, chase once, grade and log
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(cat *), Bash(date *), Bash(TZ=*), Bash(git *)
---

# Check replies

Sellers reply on whichever channel they like: an email gets answered on
WhatsApp, a WhatsApp gets a phone call back. **Check every configured channel in
one pass.** A check that covers only one channel doesn't count. Step 4 of the
`quote-loop`.

The source of truth for who was contacted, where, and with which message or
thread ID, is the contact log (default `docs/sellers-contacted.md`, or
`quote_loop.contact_log_path`).

## User overlay

Read `${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/procurement-tools/config.json`,
section `quote_loop`: `messaging.read_tool` / `send_tool` / `send_media`, `email.search_tool` /
`thread_tool` / `send_tool`, `voicemail.email_query`, `callback_phone`,
`default_locale`, and `call_via` where a tool is reached through a proxy.

Missing pieces degrade, they don't stop the check:
- no messaging tool: ask the user to paste or screenshot new chats;
- no email tools: ask the user to forward replies;
- no `voicemail` block: skip voicemail and say it is not configured;
- no `messaging.send_media`: answer a photo request in words (step 2).

Say which channels were checked and which were not.

## Steps

### 1. Collect (all channels in parallel)

**Messaging app** (`messaging.read_tool`):
- For every log row on that channel not marked avoid or closed, read the last
  ~5 messages of the chat. Chat IDs use international digits (locale
  `phone.to_international`).
- Replies may come from a different internal ID (e.g. WhatsApp `@lid`) yet still
  appear in the same chat.
- Read the delivery state of our own message (WhatsApp `ack`: SERVER sent,
  DEVICE delivered, READ read). With no reply, log "delivered, not read" or
  "read, no reply".

**Email** (`email.thread_tool`, `email.search_tool`):
- Fetch every logged thread ID in one batched call.
- Then catch replies from **new addresses**: search recent inbound mail not
  from the user (Gmail: `newer_than:3d in:inbox -from:me`) and scan senders and
  subjects for sellers. Staff often reply from a personal address.
- Bounces count as a result: log them and move that seller to its next channel.

**Voicemail** (`voicemail.email_query`, run through `email.search_tool`):
- Read each voicemail email's transcript and match the caller number to a
  seller in the log.
- No transcript: say so and give the user the recording link. Don't transcribe
  audio locally.

Convert every timestamp to the locale's timezone (`TZ=<tz> date -d @<epoch>`).

### 2. Respond

- **Answer sellers' questions from the purchase spec** (dimensions, load, fit,
  delivery city, colour, quantity). If the spec doesn't answer it, the
  question goes to the user.
- **A seller asks for a photo, picture, drawing or measurements** (the
  locale's `media_request_phrases`, e.g. "send a photo", "תשלח תמונה",
  "תמונות / תוכניות / מידות"): send the matching entries from the contact
  log's `## Reference media` table whose `send_when` includes `on_request`, as
  a quoted reply to the request (`reply_to` the seller's message ID), with
  the entry's caption. Use the route in `contact-sellers` "Reference media":
  one line saying the file is leaving the machine, stage, send, unstage.
  Log the file and the returned message ID in the seller's row. Drawings or
  measurements not in the table go to the user. No table or no
  `send_media`: describe the setup in words from the spec and tell the user.
  Only to a seller in an active enquiry, never to a group or broadcast.
- Ask the follow-ups needed to confirm **price, stock, condition (new and
  sealed), fit and delivery** in writing.
- Reply in the same thread: messaging app with a reply-to on the message being
  answered, email in the same thread ID. Local language, varied wording.
- **Never** commit to an order, payment, card details, or a full name and
  address. Say the user will get back to them (locale `templates.holding_reply`).
- **Approval:** the user asking for a reply check is approval to answer
  sellers' questions directly if the overlay has `send_without_review: true`;
  otherwise show the drafted answers first.
- **Chase at most once**, and only after the locale's
  `business_hours.chase_after_business_days` business days of silence, counted
  in the locale's business days and hours (e.g. Israel: Sun-Thu, Friday
  mornings). Mark the row "chased <date>"; never chase twice.

### 3. Grade and log

Update each seller's row:
- first reply time and time to reply (business hours only);
- what they said: recommendation, price, stock, delivery, warranty, condition;
- **grade** (the `ask-store` rubric):
  - **Responsiveness:** same business day good; next business day OK; nothing
    within the chase window is a fail.
  - **Knowledge 1-5:** did they engage with the use case, or paste a link /
    push the most expensive item?
  - **Straightness:** a clear stock answer, and a price matching the site?
  - **Tone:** helpful / neutral / pushy / dismissive.
  - **Verdict:** prefer / OK / avoid. "Avoid" stands even when cheapest.
- the message or thread ID of anything sent.

Update the log's **Best offer** line if the ranking changed (use
`quote-compare` when there are two or more confirmed offers). If the workspace
is a git repo, commit naming the sellers who replied, and push.

### 4. Report

When run by the user: one table (seller, channel, reply in one line, price),
then the current best option under the constraints, then the open items (who
hasn't replied, what needs the user's answer). No method recap.

When run on a schedule or by `quote-loop`: report **only** if a seller replied
with substance or the best option changed. A check with nothing new stays
silent.

## Data storage

Reads the user overlay (read-only) and the plugin's locale profiles. Writes only
the contact log in the user's purchase workspace.

## Notes

- Sends replies from the user's own messaging and email accounts.
- Sending reference media uploads a staged copy off the machine; it is
  deleted after the send.
- An automated bot reply (instant, generic) is logged as a bot; grade the human
  follow-up, not the bot.
