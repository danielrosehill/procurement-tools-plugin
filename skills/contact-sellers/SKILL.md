---
name: contact-sellers
description: Message shortlisted sellers by WhatsApp or email in the local language for a quote, with a reference photo when fit matters
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(cat *), Bash(date *), Bash(git *)
---

# Contact sellers

First contact with shortlisted sellers: ask for their recommendation and a
checkable quote, in a short message in the seller's language, on the channel
they actually answer. Step 3 of the `quote-loop`. Absorbs
`israel-shopping:ask-store`.

How a seller answers a pre-sale question is a cheap preview of how it treats
you after the sale, especially where returns are hard (see the locale's
`cultural_notes`). So the message is built to be gradeable: an open
recommendation question, then concrete questions with checkable answers.

## Inputs

- The shortlist from `seller-shortlist` (or sellers the user names), each with a
  channel and address.
- The purchase spec: item, use case in one line, rough budget, fit questions,
  delivery city.
- Locale profile `${CLAUDE_PLUGIN_ROOT}/locales/<locale>.json`, chosen as in
  `seller-shortlist`.
- The contact log (default `docs/sellers-contacted.md`, or
  `quote_loop.contact_log_path`), including its optional `## Reference media`
  table: workspace-relative path, caption in the local language, `send_when`
  (`on_request`, `first_contact`, or both).

## User overlay

Read `${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/procurement-tools/config.json`,
section `quote_loop`:

- `callback_phone`: the number to give sellers. Absent: give none and ask
  sellers to reply on the channel used.
- `messaging.send_tool` / `email.send_tool` (and `call_via`, when the tool is
  reached through a proxy such as a gateway's `call_tool`): the user's own
  messaging and email tools, e.g. a WAHA-backed WhatsApp MCP and a Gmail MCP.
  Absent: fall back to links and drafts (step 4).
- `messaging.send_media`: how to send an image (staging command, media-send
  tool, body shape). See "Reference media" below. Absent: describe the setup
  in words instead and tell the user once that image sending isn't configured.
- `send_without_review`: see step 3.

## Steps

1. **Dedupe once more.** Re-read the log just before sending. Skip any seller
   whose operator already has a first-contact row.
2. **Draft one message per seller.** Rules:
   - The locale's language and register, **2-4 lines**. Model names stay in
     Latin script. No long specs.
   - **Ask for their recommendation first**, with the use case in one line and a
     rough budget, then name the candidate model. The open question shows
     whether they know the category; the named model tests stock and price
     honesty.
   - Then: stock, price, delivery (days and cost to the user's city),
     **condition: new and sealed, not display or outlet**, and fit (the one fit
     question that matters for this purchase).
   - Give the callback number if the overlay has one. No other personal details.
   - Don't quote competitors' prices unless the user wants to negotiate.
   - **Reference media.** If the log declares entries with `send_when`
     including `first_contact`, attach them when the seller is made-to-order
     (workshop, carpenter, fabricator, custom job) or the message is mainly a
     "what would you recommend" ask. Skip them for a plain stock or price check
     on a known model. Mark the drafts that carry an image.
   - **Vary the wording for every seller.** Start from the locale's
     `templates.first_contact`, but change the greeting, order and phrasing each
     time. Identical bulk messages to strangers get WhatsApp accounts banned.
     The questions stay the same so the replies stay comparable; the words
     don't.
3. **Approval.** By default show the user every draft with its destination and
   send only the ones they approve. Send directly, without review, when the
   overlay says `send_without_review: true` or the user explicitly asked you to
   contact the sellers in this conversation.
4. **Send** on the locale's channel order:
   - **Messaging app** via the overlay's `messaging.send_tool`, from the user's
     own account so replies come back to them. Chat IDs use international digits
     (the locale's `phone.to_international`). No tool: give a
     `wa.me/<digits>?text=<urlencoded>` link per seller for the user to tap.
   - **Email** via `email.send_tool`, subject naming the product. No tool: give
     the draft and address.
   - **Site chat or form**: through a real browser if available, otherwise hand
     the draft to the user.
   - **Phone**: write a short call script in the local language for the user.
     The agent does not phone.
   - **With reference media**: send the text first, then the image as a
     follow-up with its caption (or the image with the first message as its
     caption when the tool supports one message only). Route: "Reference
     media" below.
5. **Log at send time**, one row per seller per channel, before moving to the
   next seller: seller, operator, product, channel and address, **message or
   thread ID** returned by the send tool, sent time in the locale's timezone,
   delivery status. An image send gets its own row note: file, caption and
   its message ID. A send that fails (bounce, unknown number) still gets a row
   saying so, then try the next channel.
6. If the workspace is a git repo, commit the log with a message naming the
   sellers contacted, and push.

## Reference media

The purchase workspace declares its media in the contact log's
`## Reference media` table. The files are the user's and stay in the workspace;
never copy them into plugin data.

Most messaging tools take a URL, not a local path, so the overlay's
`quote_loop.messaging.send_media` describes the route:

- `stage_command` / `unstage_command`: turn a local file into a short-lived URL
  and remove it afterwards (e.g. a script printing `{url, ...}` JSON, and its
  delete form taking fields from that JSON).
- `tool` (and `call_via`): the media-send tool.
- `body`: its body shape, with placeholders. WAHA example: POST
  `/api/sendImage` with `{session, chatId, file: {mimetype, filename, url},
  caption, reply_to}`. The `chatId` must be the seller's real chat ID (digits
  plus suffix), not an alias.
- `notes`: anything the user wants applied (e.g. a line before staging).

Email: attach the file through the email tool's attachment option (by path or
by staged URL, whichever it accepts).

Per send: say in one line that the file is leaving the machine, stage it, send,
log the message ID, then run the unstage command, even if the send failed.
No `send_media`: tell the user and describe the setup in words in the message.

**Privacy.** Reference photos may show a home interior. Send them only to
sellers in an active enquiry (a row in the log), never to group chats, channels
or broadcast lists.

## Data storage

Reads the user overlay (read-only), the plugin's locale profiles and the
reference media files in the workspace. Writes only the contact log in the
user's purchase workspace. Staged copies are deleted after each send.

## Notes

- **Sends messages from the user's own accounts.** That is the point (replies
  come back to them), and also why the approval rule in step 3 exists.
- **Uploads files off the machine** when sending reference media, through the
  user's staging route; the staged copy is short-lived and removed after send.
- Never offer to order, pay or give a full name and address. That is the
  user's call, always.
- A seller with only a phone number gets a call script, not a skipped row: the
  phone-only sellers are often the specialists.
