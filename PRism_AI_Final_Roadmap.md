# PRism AI — Final 24-Hour Execution Roadmap (Merged Version)

```
0h ─── 3h ─── 7h ─── 12h ─── 16h ─── 20h ─── 24h
 │      │      │       │       │       │       │
Scaffold ► Prompt ► UI Build ► Connect ► Polish ► Pitch
```

---

## Phase 1: Scaffolding & GitHub Scraper — Hours 0:00–3:00

**Goal:** Prove you can pull real PR data from any public GitHub URL before writing a line of AI or UI code.

- **[0:00–0:30] Environment Init**
  - [ ] Create root folder with `/backend` (FastAPI) and `/frontend` (React + Vite or Next.js)
  - [ ] `python -m venv venv && source venv/bin/activate`
  - [ ] `pip install fastapi google-genai httpx pydantic uvicorn python-dotenv`
  - [ ] `npm create vite@latest frontend -- --template react` → `npm install tailwindcss lucide-react`
  - [ ] `git init`, push an empty repo now — you want commit history for judges

- **[0:30–1:30] Parser & Keys**
  - [ ] Write `parse_github_url()` — regex extracting `owner`, `repo`, `pr_number` from a standard PR URL
  - [ ] Test it against 3–4 real PR URL formats
  - [ ] Set up `.env`: `GEMINI_API_KEY`, `GITHUB_TOKEN` (personal classic token — avoids public rate limits)
  - [ ] Add `.env` to `.gitignore` immediately

- **[1:30–3:00] Verify the Scraper Pipes**
  - [ ] `GET /repos/{owner}/{repo}/pulls/{number}` → title, description
  - [ ] `GET /repos/{owner}/{repo}/pulls/{number}/files` → filenames, patch diffs
  - [ ] `GET /repos/{owner}/{repo}/commits/{head_sha}/check-runs` → live CI/test status
  - [ ] Run `uvicorn main:app --reload`, hit it with curl/Postman, confirm raw JSON with real patch data comes back

**✅ Checkpoint (3h):** Paste any real PR URL into a script → see title, diff, and CI status printed in your terminal.

---

## Phase 2: Multi-Agent Prompt Engineering — Hours 3:00–7:00

**Goal:** Bulletproof structured JSON from the LLM, every single time, no exceptions.

- **[3:00–4:30] Draft the System Prompt**
  - [ ] Write the single high-density prompt instructing the model to simulate 3 personas: Security, Architecture, Testing
  - [ ] Be explicit: each agent's notes must be grounded in the actual diff/check-run data provided, not generic advice

- **[4:30–6:00] Enforce the Schema**
  - [ ] Define `PRismVerdict` Pydantic model: `verdict`, `confidence_score`, `security_agent_notes`, `architecture_agent_notes`, `testing_agent_notes`, `primary_reasoning`
  - [ ] Constrain `verdict` to exactly 3 strings your UI expects — mismatches silently break the frontend
  - [ ] Wire schema into `generate_content(..., response_mime_type="application/json", response_schema=PRismVerdict)`
  - [ ] Set `temperature=0.1` for consistency

- **[6:00–7:00] Edge Case Testing**
  - [ ] Test a PR with zero description
  - [ ] Test a PR with failing checks → confirm verdict correctly flips to `BLOCKED`/`CAUTION`
  - [ ] Test a >5-file PR → confirm graceful truncation, no crash
  - [ ] Test a malformed URL → confirm clean 400 error, not a stack trace

**✅ Checkpoint (7h):** Hitting the endpoint with a known PR reliably returns correct, well-reasoned JSON in under ~10 seconds.

---

## Phase 3: Control Tower UI Build — Hours 7:00–12:00

**Goal:** A dark, professional dashboard — this is what catches a judge's eye first.

- **[7:00–9:00] Layout & Nav**
  - [ ] Dark theme base (`bg-zinc-950` / `bg-neutral-950`)
  - [ ] Header: `🎛️ PRism AI — Live Triage Control Tower`
  - [ ] URL input field + accent button ("Launch Core Inspection")

- **[9:00–11:00] Metrics Grid**
  - [ ] Primary verdict banner card — border/background color shifts based on verdict string
  - [ ] Three-column responsive grid: 🛡️ Security / 📐 Architecture / 🧪 Testing cards
  - [ ] Confidence score in large bold typography

- **[11:00–12:00] Loading State Animation**
  - [ ] Spinner + rotating status text: *"Scraping GitHub diff arrays…"* → *"Orchestrating agent debate engine…"*
  - [ ] Fade-in transition when results render

**✅ Checkpoint (12h):** UI looks complete and polished even with fake/placeholder data plugged in manually.

---

## Phase 4: Connect Frontend to Live API — Hours 12:00–16:00

**Goal:** Replace every placeholder with real, end-to-end live data.

- **[12:00–13:30] Wire the Fetch**
  - [ ] Async `onSubmit` handler → POST to `/api/analyze-live-pr`
  - [ ] Bind input state to the URL field

- **[13:30–15:00] Data Mapping**
  - [ ] `JSON.parse()` the response, map straight into dashboard state
  - [ ] Confirm confidence %, verdict badge, and all 3 agent cards populate correctly and smoothly

- **[15:00–16:00] Bulletproof Error Handling**
  - [ ] Wrap fetch in try/catch
  - [ ] Bad URL / 404 / rate-limit → clean red error banner, never a raw error dump, loading state always clears

**✅ Checkpoint (16h):** A teammate who's never seen the code can paste a URL and get a correct result with zero explanation.

---

## Phase 5: Pre-Pitch Polish & Safe Anchors — Hours 16:00–20:00

**Goal:** Insulate the live demo from bad wifi, bad luck, and bad URLs.

- **[16:00–17:30] Two-Chip Demo Anchors** *(the key upgrade — don't skip this)*
  - [ ] Add two labeled quick-fill chips under the URL bar:
    - ⚡ **"Try Safe Hotfix PR"** → auto-fills a verified clean PR → shows a green **READY TO MERGE** result
    - ⚡ **"Try Compromised Query PR"** → auto-fills a verified risky/failing PR → shows a red **BLOCKED** result
  - [ ] This lets you demonstrate both outcomes live without typing anything on stage

- **[17:30–19:00] Scannability Pass**
  - [ ] Tighten line spacing / font sizing on evidence text so it's readable from the back of the room or on a shared screen
  - [ ] Confirm all card text wraps cleanly, nothing overflows on smaller projector resolutions

- **[19:00–20:00] Full Cold-Start Test**
  - [ ] Disconnect and reconnect to a **different** network (e.g. phone hotspot) — venue wifi is unreliable
  - [ ] Clear browser cache/dev tools storage, reload from scratch, run both quick-fill chips end-to-end
  - [ ] Take backup screenshots of both successful results in case live demo fails on stage

**✅ Checkpoint (20h):** You can survive a bad network, a rate limit, or a malformed URL without the demo visibly breaking.

---

## Phase 6: Pitch Deck & Rehearsal — Hours 20:00–24:00

**Goal:** A tight ~3-minute story that a strong build shouldn't have to carry alone.

- **[20:00–21:30] Slide Structure**
  1. **The Hook** — line-by-line comment bots overwhelm maintainers; PRism AI is the macro decision control tower instead
  2. **The Architecture** — lightweight design: real GitHub Check Runs for live CI context, no expensive sandboxing, verdict in under ~10s
  3. **Live Demo** — switch to browser, use your two quick-fill chips
  4. **What's Next** — webhook automation, full-repo semantic indexing (shows vision beyond the 24h build)

- **[21:30–23:00] Rehearse & Time It**
  - [ ] Full run-through, aim for demo core value points within ~90 seconds
  - [ ] Prep answers for: *"Is this hardcoded?"* / *"What about huge PRs?"* / *"How is this different from CodeRabbit?"*
  - [ ] Do at least 2 full timed run-throughs

- **[23:00–24:00] Buffer Zone**
  - [ ] Charge devices, close unnecessary tabs/apps, silence notifications
  - [ ] Deep breath — you're done

---

## Quick Reference: Checkpoints

| Hour | You should be able to... |
|---|---|
| 3 | Print raw GitHub PR data from a pasted URL |
| 7 | Get a reliable, correct verdict JSON from a known demo PR |
| 12 | Show a fully polished dashboard UI (even with placeholder data) |
| 16 | Have a friend use the full live UI with zero guidance |
| 20 | Survive a network switch, rate limit, or bad URL without breaking |
| 24 | Deliver the pitch twice, timed, without notes |
