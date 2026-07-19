# read-along evaluation workspace

Output from Anthropic's [`/skill-creator`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/skill-creator/skills/skill-creator/SKILL.md) trigger-eval run against **read-along** (version 5, 2026-07-18). This is a teaching artifact with an unusual headline: the trigger-eval apparatus **structurally cannot measure this skill**, and that finding is the point of the snapshot. See the [eval section of the main README](../README.md).

## The one-line takeaway

read-along is an *agentic workflow* skill: given a real request it starts DOING the work (`gh pr list`, reading `work/` notes) instead of consulting a skill first. `run_eval.py` only counts a trigger when the model's FIRST tool call is `Skill` or `Read`; the first action trips an early-return and scores "not triggered." So the 0% positive-trigger result is a measurement artifact, not a description defect. The description was reviewed by hand instead and kept verbatim.

## Files in this folder

- **`trigger-eval.json`** — 20 real-world queries: 10 that *should* trigger read-along (overnight-run walkthroughs, pre-demo tours, scoped `/read-along PRs 40-60`, archaeology-mode "tour how this repo evolved"), 10 that *shouldn't*. The negatives are deliberately tricky near-misses that share keywords: review a single PR (code-review), a slide deck "for the demo" (branded-pptx), "write a children's storybook" (storybook keyword), "the overnight run left failing tests, fix them" (overnight-run keyword, wants a fix), a podcast "I can listen to" (read-along has audio narration).
- **`run-results/`** — captured output from `scripts.run_loop` (gitignored). Machine-specific, noisy, and fully reproducible from `trigger-eval.json`. Regenerate locally with the command below.
- *(No `eval_review.html` this time.* The `--report` HTML would headline the misleading 0% recall and show zero description changes, so this README is the human-consumable artifact instead. This is a deliberate deviation from the branded-docx layout.)*

## Results (2026-07-18)

| Check | Result |
|---|---|
| Trigger-eval loop ran end-to-end | ✅ 20 queries × 3 runs × 5 iterations |
| Negative queries correctly don't trigger | ✅ 10 / 10 (but see caveat) |
| Skill fires on natural-language queries (under automated test) | ⚠️ 0 / 10 — measurement artifact, see below |
| Description improvement loop produced a better candidate | ❌ 5 iterations, `best_description == original` (score pinned at 6/12 train, 4/8 test) |
| Description reviewed qualitatively against skill-creator rubric | ✅ Strong; kept verbatim |

**Why the negatives passing is not the reassurance it looks like:** when a skill structurally never registers as "triggered," the negatives pass for free — nothing fires either way. So even the 10/10 negative result carries little signal here. The genuinely informative work was the qualitative review (progressive disclosure, why-behind-rules, no over-fitting to the origin project), not these numbers.

## Why this eval is uninformative for THIS class of skill

`run_eval.py` writes a throwaway command file `.claude/commands/read-along-skill-<uuid>.md` containing only the description string (it never loads the real installed skill), runs `claude -p <query>`, and counts a trigger only if the first tool call is `Skill`/`Read` pointing at that uuid name. Line ~141: any other first tool call (`Bash`, `Glob`, `gh ...`) returns `False` immediately. The harness was built for consult-before-acting document skills (branded-docx); it is blind to a fire-by-acting workflow skill. A literal `/read-along PRs 40-60` query also can't match, because the registered command is uuid-suffixed, not the real `/read-along`.

## What to do instead of trusting the recall number

- [ ] **Judge the description by hand.** For interactive/workflow Claude Code skills, the trigger-eval recall is not a valid signal — review the description against the rubric directly.
- [ ] **If you want an empirical triggering check**, open a fresh Claude Code session on a real repo and type a natural query; watch whether read-along actually engages. That exercises the real installed skill, which `run_eval` never touches.
- [ ] **Keep the negative set.** It is still the cheap guard against a future description rewrite starting to over-trigger on adjacent tasks.

## How to regenerate

```bash
python -m scripts.run_loop \
  --eval-set read-along-workspace/trigger-eval.json \
  --skill-path skills/read-along \
  --model claude-opus-4-8 \
  --max-iterations 5 \
  --runs-per-query 3 \
  --report none \
  --results-dir read-along-workspace/run-results \
  --verbose
```

Run from the skill-creator directory (so `python -m scripts.run_loop` resolves). Paths above are relative to this repo root; adjust if you run from elsewhere.
