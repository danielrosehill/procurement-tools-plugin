# Sellers contacted: <purchase> enquiries and responsiveness

<!-- Template from the procurement-tools quote loop. Copy to docs/sellers-contacted.md in the purchase workspace. The quote-loop skills read and write this file; keep the table columns as they are. -->

Part of the point of these enquiries is to find out **which sellers actually respond and care**, not only who is cheapest. A seller's pre-sale answer previews its after-sale service.

**Item:** <what is being bought, with the key spec in one line>
**Locale:** <locale profile, e.g. israel> (all times in <timezone>)
**Constraints:** reputable sellers only: <yes/no>; new and sealed only: <yes/no>; excluded sellers: <list or none>
**Every enquiry asks:** a recommendation for the use case, stock, price, delivery (days and cost), condition (new and sealed, not display or outlet), fit (<the fit question>).
**Callback number given:** <from the user overlay, or none>

**Grading:**
- **Responsiveness:** a reply the same business day is good, the next business day is OK, nothing within <N> business days is a fail.
- **Knowledge (1-5):** did they engage with the use case, or paste a link / push the most expensive item?
- **Straightness:** a clear stock answer, with a price that matches the site.
- **Tone:** helpful / neutral / pushy / dismissive.
- **Verdict:** prefer / OK / avoid. "Avoid" counts against a seller even when it is cheapest.

Chase each seller once at most. One row per seller per channel. "Operator" names the company behind a storefront, so sister brands and shared operators are deduped.

## Reference media

<!-- Optional. Photos, drawings or measurements of the user's setup that help a seller recommend or quote. Files stay in this workspace; paths are relative to its root. send_when: on_request (a seller asks for a photo, drawing or measurements), first_contact (attach to the first message for made-to-order, workshop or "what would you recommend" enquiries), or both: "on_request, first_contact". Captions in the locale's language. Delete the rows, or leave the table empty, if there is nothing to send. Sent only to sellers in an active enquiry, never to groups or broadcasts. -->

| Path | Caption | send_when |
|---|---|---|
| <photos/current-setup.jpg> | <one line in the local language> | <on_request, first_contact> |

## Best offer

<!-- One line, updated whenever the ranking changes: seller, product, total delivered price, condition, lead time, what is still unconfirmed. -->
None yet.

## Log

| Seller | Operator / sister brands | Product asked about | Channel / address | Message or thread ID | Sent | Delivery status | First reply | Time to reply | Recommendation | Knowledge | Stock / price answer | Condition | Tone | Verdict | Chased |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Excluded or skipped

<!-- Sellers found but not contacted, with the reason (aggregator, excluded by the user, used-only, duplicate of <operator>). Stops the next research pass from re-finding them. -->

| Seller | Reason | Date |
|---|---|---|
