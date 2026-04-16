# branded-docx evaluation workspace

Fresh output from Anthropic's [`/skill-creator`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/skill-creator/skills/skill-creator/SKILL.md) run against **v2.5.0** of branded-docx. Teaching artifact for the [eval section of the main README](../README.md#why-i-evaluate-my-skills-and-you-should-too).

## Files in this folder

- **`trigger-eval.json`** — 20 real-world queries: 10 that *should* trigger branded-docx (covering all four brands, including glasses-wearer cases for Accessible), 10 that *shouldn't*. Negatives are deliberately tricky: editing a brand file, a PowerPoint in RE/MAX colours, a large-print PDF sign — all close enough to trip a naive keyword match.
- **`eval_review.html`** — self-contained browser UI with the current v2.5.0 description embedded. Open directly, click through to review/toggle/export. No server.
- **`run-results/`** — captured output from `scripts.run_loop` (gitignored). Regenerate locally with the command below if you want the raw data.

## Current status

| Check | Status |
|---|---|
| Description fits 1024-char upload cap | ✅ 964 / 1024 (60-char margin) |
| Trigger-eval loop ran end-to-end | ✅ 20 queries × 3 runs × 5 iterations |
| Negative queries correctly don't trigger | ✅ 10 / 10 |
| Skill fires on natural-language queries (under automated test) | ⚠️ 0 / 10 — the test checks one specific invocation path; whether the skill fires via other paths is still unverified (see Q1) |
| Description improvement loop produced a better candidate | ❌ Loop proposed 4 rewrites; none scored higher than the original |
| Behaviour evals (does the .docx come out on-brand?) | ⬜ Not started |
| Natural-language invocation path verified | ⬜ Not verified |

**Honest read:** the trigger-eval apparatus runs cleanly and gives real signal on negatives. The 0 / 10 positive result isn't necessarily a broken skill — `run_eval.py` measures only the SlashCommand invocation path, not the `Skill` tool or direct user invocation — but it is a real open question. No description rewrite was applied because none of the loop's candidates scored any better; the bottleneck is likely measurement scope, not wording.

## Open questions / next eval cycle

- [ ] **Q1 — Resolve the 0% positive-trigger ambiguity.** Open a fresh Claude Code session, type a natural query ("convert this markdown to a branded .docx in coral style"), and check the stream for either a `Skill` tool call or a Read of `SKILL.md`. If it fires, the eval was measuring the wrong path and this skill is fine for real usage. If it doesn't, the description genuinely needs rework.
- [ ] **Q2 — Add behaviour evals.** Write 3–5 prompts with output assertions: *output is valid .docx*, *cover page contains the navy accent bar*, *footer has the supplied contact info*, *brand token colours are applied in headings*. This is the layer that gives an unambiguous "the skill works" verdict.
- [ ] **Q3 — Re-run trigger evals on every description change.** Silent 1024-char cap violations are one bad commit away; any material rewrite needs a full loop + per-query inspection, not just a character count.

## How to regenerate

```bash
# Windows needs UTF-8 forced — run_loop writes a ✗ char to a live HTML report
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m scripts.run_loop \
  --eval-set branded-docx-workspace/trigger-eval.json \
  --skill-path skills/branded-docx \
  --model claude-opus-4-6 \
  --max-iterations 5 \
  --results-dir branded-docx-workspace/run-results \
  --verbose
```

Run from the skill-creator directory (`~/.claude/skills/skill-creator` on most installs) so `python -m scripts.run_loop` resolves.
