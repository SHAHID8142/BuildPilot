# Step-by-Step User Guidance (external platform actions)

When a task requires the USER to do something on an external platform —
collecting an API key, creating a webhook endpoint in a dashboard, granting
OAuth consent, pointing DNS records, accepting a license, inviting a service
account — the agent does NOT dump a paragraph of instructions and wait.

## The law

**One step at a time.** The agent:

1. Says what the overall goal is (one sentence: "we need a Stripe API key so
   checkout can charge cards").
2. Gives exactly ONE instruction — the single next physical action
   ("1. Open https://dashboard.stripe.com/apikeys and log in").
3. STOPS and waits for the user to confirm it's done (or paste what they
   see, or ask a question).
4. Only then gives the next single step.

## Rules

- **Never batch steps.** A wall of "1. do X 2. do Y 3. do Z" gets skimmed,
  and step 3 always depends on what step 1 actually looked like.
- **Never guess UI labels.** Say what to accomplish ("find the API keys
  section, usually under Developers or Settings") and ask for a screenshot/
  paste when the label is uncertain — dashboards change constantly.
- **Secrets stay secret**: when the user must paste a key, tell them they
  can mask it (`sk_live_…abc123`) — the agent only needs to know WHICH key
  it is, not its value. The user then puts the real value into `.env`
  themselves. The agent never asks for full secrets in chat.
- **Security-sensitive actions get an extra beat**: before the user grants
  OAuth scopes, deletes a resource, or changes DNS, the agent states the
  consequence in one line ("this gives the app read access to your repos").
- **Timeouts and propagation are stated up front** when relevant ("DNS can
  take up to 48h; we'll verify before moving on").
- **If the user gets stuck twice on the same step**, offer the alternative
  path (different browser, different account role, manual upload) instead
  of repeating the same words louder.
- Track progress in `.sps/handoff.md` (which platform steps are done) so a
  session break doesn't restart the dance from step 1.

## Why

Platform dashboards are the one surface the agent cannot see or verify.
Single steps keep the user's actions correct, keep secrets out of the
transcript, and turn a confusing chore into a checklist the user finishes
in one sitting.
