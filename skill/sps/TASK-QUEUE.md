# Task Queue Law (No Task Dropping)

**Law:** the agent FINISHES the current task before starting anything new.
Newly received tasks are QUEUED, never started mid-task.

## The rule

1. **Current task owns the agent.** While a task is `doing`, every incoming
   user message or event that requests new work is appended to the todo queue
   (`./.sps/section-todos/<section>.md`, or `./.sps/task-queue.md` for
   cross-section tasks) with status `todo` — and nothing else.
2. **No preemption.** Dropping a `doing` task to start a newer request is a
   process violation, even if the new request looks urgent. The only
   exceptions: the user explicitly says "abort/switch now", or the current
   task is blocked (then mark it `blocked`, record why, and pick the next
   queued item).
3. **Queue, acknowledge, continue.** When a new task arrives mid-task, write
   it to the queue, tell the user it is queued and when it will run, and
   keep working. Do not ask whether to switch.
4. **Drain order.** Process the queue strictly in the order written, oldest
   first, unless the user reorders it. Each queued item gets the same
   plan/verify/handoff discipline as any other task.
5. **Mid-turn messages.** A message arriving alongside a tool result is a
   queue item, not an interrupt — same as rule 1.

## Session start

On every session start (or resume), read `./.sps/task-queue.md` first:
finish or resume any `doing` item before touching `todo` items.

## Template for `./.sps/task-queue.md`

```markdown
# Task Queue
## doing
- [ ] id: T-<n> task: … started: <date>
## queued (oldest first)
- [ ] id: T-<n+1> task: … received: <date> source: user
## done
- [x] id: T-<n-1> task: … finished: <date>
```
