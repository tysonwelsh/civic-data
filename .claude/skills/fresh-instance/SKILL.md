---
name: fresh-instance
description: Launch a fresh, remote-controllable Claude Code session in this repo, primed from HANDOFF.md — so a long-context session can hand off to a clean one without the user being at the desk. Use when the user says "start a fresh instance", "spin up a new session", "hand off to a new Claude", "context is getting long — relaunch", or similar.
---

# Fresh instance — hand off to a new remote-controllable session

Launches a NEW interactive Claude Code session in `/Users/tysonwelsh/civic-data`,
detached under tmux with `--remote-control` enabled, primed with a kickoff prompt that
points it at `HANDOFF.md`, then opens a visible Terminal window attached to it. The
current (long-context) session stays alive until the user abandons it. Verified working
2026-07-16 on Claude Code 2.1.211 / tmux via Homebrew; Terminal-window step verified
2026-07-19.

**Why tmux, not screen or `--bg`:** the interactive TUI needs a pty to keep polling for
remote messages; tmux provides one and `capture-pane` lets you verify the launch. macOS's
ancient bundled `screen` (4.00) was tested and is unreliable here (the kickoff prompt
never auto-submits, and hardcopy can't capture the TUI). `claude --bg` background agents
are not the same surface as Remote Control sessions — don't substitute one.

**Sandbox note:** run every tmux/launch command with the Bash sandbox DISABLED
(`dangerouslyDisableSandbox: true`) — the spawned session must outlive the command and
needs network + keychain access. Use only short `sleep`s (long foreground sleeps are
blocked by the harness).

## Procedure

### 1. Bring the handoff current (before launching)

The fresh instance knows only what's on disk. Update `HANDOFF.md` with anything from
THIS conversation not yet recorded, following its existing structure:

- work completed this session (move it under "Where things stand");
- **in-flight work**: the exact stopping point, what's verified vs pending, next command
  to run;
- decisions the user made this session (approvals, scope calls, priority changes);
- new operational gotchas discovered.

Also check off / annotate `TODO.md` items completed this session, per repo convention.
Facts only from this conversation — never fabricate or pad. If the session did nothing
repo-relevant, skip this step entirely.

### 2. Compose the kickoff prompt

Write it to a scratchpad file (avoids shell-quoting hazards). Base text:

> Fresh session taking over from a previous instance whose context ran long. Read
> HANDOFF.md and TODO.md (queue = [DEBT]+[GATED]+PUBLISH GATE; options live in LEADS.md;
> standing rules in GOTCHAS.md), then post a brief status summary — what's done, what's
> in flight, and the prioritized next tasks — and STOP. Wait for direction; do not start
> any work until instructed.

If the outgoing session has immediate context worth carrying (e.g. "pick up at step 3 of
the SOVC re-parse — the probe already ran"), append 1–3 sentences. Keep the whole prompt
under ~15 lines; the durable detail belongs in HANDOFF.md, not the prompt.

### 3. Launch

```bash
NAME="fresh-$(date +%m%d-%H%M)"
PROMPT_FILE=<scratchpad>/kickoff.txt   # written in step 2
tmux new-session -d -s "$NAME" -x 200 -y 50 -c /Users/tysonwelsh/civic-data \
  "claude --remote-control=$NAME \"\$(cat $PROMPT_FILE)\""
```

Notes:
- The tmux session name and the Remote Control session name are kept identical on
  purpose — one handle for both.
- The positional prompt auto-submits once the TUI is up (verified); no keystroke
  injection needed.
- The new session inherits the user's default model/effort/permission settings. Don't
  pass `--permission-mode` overrides — permission prompts are answerable from the
  Remote Control UI on the phone.
- If tmux is missing (fresh machine): `brew install tmux`. Do NOT fall back to `screen`
  (see above).

### 4. Verify (~10 s after launch)

```bash
sleep 10; tmux capture-pane -t "$NAME" -p | grep -v '^$' | tail -25
```

Confirm, in the captured pane:
1. the Claude Code banner (session actually started);
2. the line `/remote-control is active · … https://claude.ai/code/session_…` —
   **capture that URL**, it's the direct link to the new session;
3. the kickoff prompt echoed and a `⏺` response underway (prompt submitted).

If instead the pane shows a dialog or error (trust prompt, auth failure, update nag),
report it verbatim and resolve before declaring success. If the pane is empty, wait 5 s
and recapture once before diagnosing.

### 5. Open a visible Terminal window attached to the session

tmux sessions are detached (headless) — the user sees nothing until something attaches.
Open a macOS Terminal window on it (verified working 2026-07-19; sandbox DISABLED, same
as every tmux command in this skill):

```bash
osascript -e 'tell application "Terminal"
  do script "tmux attach -t '"$NAME"'"
  activate
end tell'
sleep 3; tmux ls   # the session should now show "(attached)"
```

Notes:
- First run may trigger a one-time macOS Automation permission prompt ("… wants to
  control Terminal") — tell the user to click OK if the window doesn't appear.
- **Closing the window does NOT kill the session** (it just detaches); re-attach anytime
  with `tmux attach -t <name>`. Clean detach from inside: `Ctrl-b` then `d`.
- Skip this step only if the user is remote-only (phone) and says they don't want a
  desktop window.

### 6. Report to the user (the final message)

- The session **name** and the **claude.ai/code session URL** from step 4 — on the
  phone, the user can tap the URL or find the name in the claude.ai/code session list.
- That a Terminal window is open on the session (and that closing it only detaches —
  the instance keeps running; `tmux attach -t <name>` re-attaches).
- That the new instance is reading the handoff and will post a status summary, then wait.
- That this old session can now be abandoned (it keeps running until exited; see
  housekeeping).

### 7. Housekeeping — old sessions

`tmux ls` lists live sessions. **Never auto-kill** other `fresh-*` sessions — one of
them may be the very session the user is currently controlling (possibly the one running
this skill). Report stale-looking ones and kill only on explicit request:
`tmux kill-session -t <name>`. (Exiting a session from the phone with `/exit` also ends
its tmux session.)
