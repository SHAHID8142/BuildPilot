# BuildPilot Cheat Sheet (say this, get that)

One page. Every sentence a non-technical user ever needs. Nothing else to learn.

## Starting — what /sps asks you
- Answer the kickoff questions in one go (goal, deploy target, stack, content,
  CMS, brand, integrations, auth, mobile, timeline). Plain words are fine.
- "That's all the answers" — done with the questionnaire.
- "Confirm the platform" — your yes at gate G1; nothing is built before it.
- "Approve the plan" — your yes at gate G2; building starts after it.

## During build — approve or change
- "Approve" — yes to the section as shown.
- "Request changes: <what>" — name the thing, the agent fixes and re-asks.
- "Batch approve" — let consecutive low-risk sections run without stopping.
- "I'll do that step now" — you're on an external step (API key, DNS); say it
  when done. Never paste full secrets in chat — mask them and put real values
  in `.env` yourself.

## Checking progress
- `/sps status` — "Where am I?" (branch, task queue, after-sale clocks).
- `/sps audit` — score the project against the rules (100 points).

## When something's wrong
- `/sps doctor` — the install/host feels broken; run this first.
- "Here's what I saw: <paste the error or describe it>" — tell the agent
  exactly what happened; screenshots or pasted text both work.
- "Capture a lesson: <mistake>" — turn a mistake into a permanent rule
  (sent only when you later say send, and adopted only after you approve it).

## Finishing
- `/sps release-lock` — project done; cleanly removes the workflow lock.
- After-sale clocks: every completed job includes 1 month all-type support +
  1 month free SEO, counted from delivery. `/sps status` shows days remaining;
  at day 30 you get a closing report and paid-continuation options. Nothing
  continues silently.

Full guide: [USER-GUIDE.md](../../USER-GUIDE.md).
