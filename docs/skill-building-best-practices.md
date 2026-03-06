# The Complete Guide to Building Skills for Claude

Distilled from [Anthropic's official guide](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) (January 2026). Use this as a reference when creating or reviewing skills in this repo.

---

## What is a skill?

A skill is a folder containing:

- **SKILL.md** (required) — Instructions in Markdown with YAML frontmatter
- **scripts/** (optional) — Executable code (Python, Bash, etc.)
- **references/** (optional) — Documentation loaded as needed
- **assets/** (optional) — Templates, fonts, icons used in output

Skills use **progressive disclosure** (three levels):

1. **First level (YAML frontmatter):** Always loaded in Claude's system prompt. Provides just enough for Claude to know *when* each skill should be used — without loading everything into context.
2. **Second level (SKILL.md body):** Loaded when Claude thinks the skill is relevant. Contains full instructions and guidance.
3. **Third level (Linked files):** Additional files bundled in the skill directory that Claude can choose to navigate and discover only as needed.

---

## YAML Frontmatter — The Most Important Part

The frontmatter is how Claude decides whether to load your skill.

### Minimal required format

```yaml
---
name: your-skill-name
description: What it does. Use when user asks to [specific phrases].
---
```

### Field requirements

**name** (required):
- kebab-case only
- No spaces or capitals
- Should match folder name

**description** (required):
- MUST include BOTH: what the skill does + when to use it (trigger conditions)
- Under 1024 characters
- No XML tags (`<` or `>`)
- Include specific tasks users might say
- Mention file types if relevant
- Structure: `[What it does] + [When to use it] + [Key capabilities]`

**license** (optional):
- Use if making skill open source
- Common: MIT, Apache-2.0

**compatibility** (optional):
- 1-500 characters
- Indicates environment requirements: intended product, required system packages, network access needs

**metadata** (optional):
- Any custom key-value pairs
- Suggested: `author`, `version`, `mcp-server`
- Example:
  ```yaml
  metadata:
    author: ProjectHub
    version: 1.0.0
    mcp-server: projecthub
  ```

### Security restrictions

**Forbidden in frontmatter:**
- XML angle brackets (`<` `>`)
- Skills with "claude" or "anthropic" in `name` (reserved)

Why: Frontmatter appears in Claude's system prompt. Malicious content could inject instructions.

---

## Critical Rules

### SKILL.md naming
- Must be exactly `SKILL.md` (case-sensitive)
- No variations: SKILL.MD, skill.md — these will fail

### Skill folder naming
- Use kebab-case: `notion-project-setup`
- No spaces: ~~`Notion Project Setup`~~
- No underscores: ~~`notion_project_setup`~~
- No capitals: ~~`NotionProjectSetup`~~

### No README.md inside the skill folder
- Don't include README.md inside your skill folder
- All documentation goes in SKILL.md or references/
- Note: when distributing via GitHub, you'll still want a repo-level README for human visitors — this is separate from the skill folder

---

## Writing Effective Descriptions

### Good descriptions (specific, actionable, include triggers)

```yaml
# Good - specific and actionable
description: Analyzes Figma design files and generates developer handoff
  documentation. Use when user uploads .fig files, asks for "design specs",
  "component documentation", or "design-to-code handoff".

# Good - includes trigger phrases
description: Manages Linear project workflows including sprint planning,
  task creation, and status tracking. Use when user mentions "sprint",
  "Linear tasks", "project planning", or asks to "create tickets".

# Good - clear value proposition
description: End-to-end customer onboarding workflow for PayFlow. Handles
  account creation, payment setup, and subscription management. Use when
  user says "onboard new customer", "set up subscription", or
  "create PayFlow account".
```

### Bad descriptions

```yaml
# Too vague
description: Helps with projects.

# Missing triggers
description: Creates sophisticated multi-page documentation systems.

# Too technical, no user triggers
description: Implements the Project entity model with hierarchical relationships.
```

---

## Writing Main Instructions

### Recommended SKILL.md structure

```markdown
---
name: your-skill
description: [...]
---

# Your Skill Name

## Instructions

### Step 1: [First Major Step]
Clear explanation of what happens.

Example:
```bash
python scripts/fetch_data.py --project-id PROJECT_ID
Expected output: [describe what success looks like]
```

### Step 2: [Next Step]
...

## Examples

### Example 1: [common scenario]
User says: "..."
Actions:
1. ...
2. ...
Result: ...

## Troubleshooting

### Error: [Common error message]
Cause: [Why it happens]
Solution: [How to fix]
```

### Best practices for instructions

**Be specific and actionable:**
```text
# Good
Run `python scripts/validate.py --input {filename}` to check data format.
If validation fails, common issues include:
- Missing required fields (add them to the CSV)
- Invalid date formats (use YYYY-MM-DD)

# Bad
Validate the data before proceeding.
```

**Reference bundled resources clearly:**

```text
Before running queries, consult `references/api-patterns.md` for:
- Rate limiting guidance
- Pagination patterns
- Error codes and handling
```

**Use progressive disclosure:** Keep SKILL.md focused on core instructions. Move detailed documentation to `references/` and link to it.

---

## Common Skill Use Case Categories

### Category 1: Document & Asset Creation

Creating consistent, high-quality output (documents, presentations, apps, designs, code).

Key techniques:

- Embedded style guides and brand standards
- Template structures for consistent output
- Quality checklists before finalizing
- No external tools required — uses Claude's built-in capabilities

### Category 2: Workflow Automation

Multi-step processes that benefit from consistent methodology.

Key techniques:

- Step-by-step workflow with validation gates
- Templates for common structures
- Built-in review and improvement suggestions
- Iterative refinement loops

### Category 3: MCP Enhancement

Workflow guidance to enhance the tool access an MCP server provides.

Key techniques:

- Coordinates multiple MCP calls in sequence
- Embeds domain expertise
- Provides context users would otherwise need to specify
- Error handling for common MCP issues

---

## Testing

### 1. Triggering tests

Ensure your skill loads at the right times.

- Triggers on obvious tasks
- Triggers on paraphrased requests
- Doesn't trigger on unrelated topics

### 2. Functional tests

Verify the skill produces correct outputs.

- Valid outputs generated
- API calls succeed
- Error handling works
- Edge cases covered

### 3. Performance comparison
Prove the skill improves results vs. baseline.

### Quantitative metrics (aspirational targets)

- Skill triggers on 90% of relevant queries
- Completes workflow in X tool calls
- 0 failed API calls per workflow

### Qualitative metrics

- Users don't need to prompt Claude about next steps
- Workflows complete without user correction
- Consistent results across sessions

---

## Skill-Creator: Evals, Benchmarking, and A/B Testing

The skill-creator skill is built into Claude.ai and available as a Claude Code plugin (`/plugins` to install). It operates in **4 modes**:

| Mode | What it does |
| --- | --- |
| **Create** | Generates skills from natural language descriptions. Produces properly formatted SKILL.md with frontmatter, suggests trigger phrases. |
| **Eval** | Creates test cases and runs them against your skill to verify it works correctly. |
| **Improve** | Identifies what's not working, revises instructions, and optimizes trigger descriptions through iterative feedback loops. |
| **Benchmark** | Runs blind A/B comparisons between skill-enabled and no-skill runs, with variance analysis to prove the skill actually helps. |

Sources: [Anthropic's official guide](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf), [tessl.io analysis](https://tessl.io/blog/anthropic-brings-evals-to-skill-creator-heres-why-thats-a-big-deal/), [video walkthrough](https://www.youtube.com/watch?v=qXWz-V_XMOc).

### The eval pipeline — 4 sub-agents in parallel

When you run evals, skill-creator spawns composable sub-agents:

1. **Executor** — Runs the skill against eval prompts. For each test case, it spawns 2 subagents: one with the skill loaded, one without. These run in parallel (e.g., 3 test cases = 6 parallel runs).
2. **Grader** — Evaluates each output against defined assertions (specific, verifiable checks). Also runs in parallel after all executions complete.
3. **Comparator** — Performs **blind** A/B comparisons between outputs. It does not know which output used the skill and which didn't — eliminating bias.
4. **Analyzer** — Surfaces patterns that aggregate statistics might hide. Identifies when benchmark results show equal performance (meaning either test cases are too easy, or the skill targets areas where the base model already excels).

### Test case format

Each test case is a JSON file pairing a realistic user prompt with assertions:

```json
{
  "eval_id": 2,
  "eval_name": "api-handler",
  "prompt": "Review this Express handler for me — it processes orders. Any issues?",
  "assertions": [
    {
      "id": "no-input-validation",
      "text": "Flags that req.body items are used without validation",
      "type": "quality"
    },
    {
      "id": "structured-output",
      "text": "Review uses severity levels (critical/warning/suggestion)",
      "type": "format"
    }
  ]
}
```

Assertion types include `quality` (did the skill catch the right issues?) and `format` (did the output follow the right structure?).

### Two types of evals

- **Capability evals** — Is the output objectively better? (e.g., SEO audit is more thorough, PDF fields filled correctly)
- **Procedural evals** — Does the skill follow the correct workflow? (e.g., insurance claim triage: claims > $10K require police report, injury claims require medical records)

### Description optimization loop

When a skill doesn't trigger reliably, skill-creator can optimize its description:

1. Generates example prompts: cases where the skill *should* trigger, and cases where it should *not*
2. Splits prompts into a training set (60%) and test set (40%)
3. Fires queries from the training set and checks whether the skill was triggered (not fully executed — just trigger detection)
4. Iterates up to 5 times, rewriting the description each cycle to improve trigger accuracy
5. Validates against the held-out test set

This is essentially machine learning applied to prompt engineering — train/test split, iterative refinement, holdout validation.

### Benchmark output

After a benchmark run, skill-creator produces:

- **HTML reports** showing each output side-by-side, with grades
- **Pass rate comparison** (e.g., *"with skill: 13.5% higher success rate"*)
- **Timing data** (e.g., *"22% faster with skill"*)
- **Token usage** comparison
- **Assertion-level breakdown** — which specific checks passed/failed with and without the skill
- A **feedback.json** file you can drag back into Claude Code to feed improvements

### Two categories of skills (and why evals matter differently)

1. **Capability uplift** — Fills gaps in the base model (e.g., PDF form filling, DOCX generation). These skills have a **retirement date**: when the base model catches up, the skill becomes dead weight or actively harmful. Run benchmarks after each model upgrade to check if the skill still helps.

2. **Workflow/preference encoding** — Encodes your specific processes, compliance rules, or system design (e.g., NDA review checklist, release workflow, weekly report compilation). These don't expire with model upgrades but still need evals to ensure they trigger reliably and produce correct results.

> *"The answer isn't less context. It's tested context."* — The eval framework exists because untested skills can silently degrade, hold back newer models, or fail to trigger when needed. The small upfront investment in evals pays off for any skill used regularly.

### Quick start

**Claude.ai** (slash command):

```bash
# Install the plugin (Claude Code) — one of:
/plugin install skill-creator@claude-plugin-directory
/plugin > Discover > skill-creator

# Create a skill with evals
/skill-creator "Make me an SEO audit skill"
→ "yes, run evals as well"

# Evaluate an existing skill
/skill-creator "Evaluate my branded-docx skill and run test cases"

# Benchmark an existing skill
/skill-creator "Run an A/B test on my branded-docx skill"

# Optimize trigger description
/skill-creator "Optimize the description of my branded-docx skill to trigger more reliably"
```

**Claude Code** (natural language — give it the path so it knows which skill):

```text
Evaluate my branded-docx skill at skills/branded-docx/ — run test cases and benchmark it
```

The path is how skill-creator finds your `SKILL.md`. From there it:

1. Generates 2-3 realistic test prompts and shows them for your approval
2. Spawns parallel runs: one with the skill, one without (baseline)
3. Grades results and opens a side-by-side viewer for review
4. Iterates based on your feedback

For description optimization, it runs a separate automated loop — generates 20 trigger/non-trigger queries, splits 60/40 train/test, and iterates up to 5 times rewriting the description to improve trigger accuracy.

---

## Distribution and Sharing

### Current distribution model

How individual users get skills:

1. Download the skill folder
2. Zip the folder (if needed)
3. Upload to Claude.ai via Settings > Capabilities > Skills
4. Or place in Claude Code skills directory

### Organization-level skills

- Admins can deploy skills workspace-wide
- Automatic updates
- Centralized management

### Skills via API

- `/v1/skills` endpoint for listing and managing skills
- Add skills to Messages API requests via `container.skills` parameter
- Version control and management through the Claude Console
- Works with the Claude Agent SDK for building custom agents

### Recommended approach: host on GitHub

1. Public repo for open-source skills
2. Clear README with installation instructions
3. Example usage and screenshots
4. Installation guide section

### Positioning your skill

- Focus on **outcomes, not features**
- Good: *"The ProjectHub skill enables teams to set up complete project workspaces in seconds — including pages, databases, and templates — instead of spending 30 minutes on manual setup."*
- Bad: *"The ProjectHub skill is a folder containing YAML frontmatter and Markdown instructions that calls our MCP server tools."*

---

## Skill Patterns

### Pattern 1: Sequential workflow orchestration

Use when: Multi-step processes in a specific order.
Key: Explicit step ordering, dependencies between steps, validation at each stage, rollback instructions for failures.

### Pattern 2: Multi-MCP coordination

Use when: Workflows span multiple services.
Key: Clear phase separation, data passing between MCPs, validation before moving to next phase.

### Pattern 3: Iterative refinement

Use when: Output quality improves with iteration.
Key: Explicit quality criteria, iterative improvement, validation scripts, know when to stop iterating.

### Pattern 4: Context-aware tool selection

Use when: Same outcome, different tools depending on context.
Key: Clear decision criteria, fallback options, transparency about choices.

### Pattern 5: Domain-specific intelligence

Use when: Your skill adds specialized knowledge beyond tool access.
Key: Domain expertise embedded in logic, compliance before action, comprehensive documentation.

### Problem-first vs. Tool-first framing

- **Problem-first:** *"I need to set up a project workspace"* — your skill orchestrates the right MCP calls in the right sequence. Users describe outcomes; the skill handles the tools.
- **Tool-first:** *"I have Notion MCP connected"* — your skill teaches Claude the optimal workflows and best practices. Users have access; the skill provides expertise.

---

## Common Issues

### Skill won't upload

**"Could not find SKILL.md in uploaded folder"** — File not named exactly SKILL.md. Rename (case-sensitive). Verify with `ls -la`.

**"Invalid frontmatter"** — YAML formatting issue. Check for missing delimiters (`---`), unclosed quotes.

**"Invalid skill name"** — Name has spaces or capitals. Use kebab-case.

### Skill doesn't trigger

Revise your description field. Checklist:

- Is it too generic?
- Does it include trigger phrases users would actually say?
- Does it mention relevant file types?

Debug: Ask Claude *"When would you use the [skill name] skill?"* — Claude will quote the description back. Adjust based on what's missing.

### Skill triggers too often

1. Add negative triggers: *"Do NOT use for simple data exploration (use data-viz skill instead)."*
2. Be more specific in description
3. Clarify scope

### Instructions not followed

- **Too verbose** — Keep concise, use bullet points
- **Buried** — Put critical instructions at the top, use `## Important` or `## Critical` headers
- **Ambiguous** — Be explicit: *"CRITICAL: Before calling create_project, verify: project name is non-empty, at least one team member assigned"*

### Large context issues

Symptom: Skill seems slow or responses degraded.
Solutions:

1. Optimize SKILL.md size: move detailed docs to references/, link instead of inline, keep SKILL.md under 5,000 words
2. Reduce enabled skills: evaluate if you have more than 20-50 skills enabled simultaneously

---

## Key Design Principles

- **Composability:** Claude can load multiple skills simultaneously. Your skill should work well alongside others.
- **Portability:** Skills work identically across Claude.ai, Claude Code, and API. Create a skill once and it works across all surfaces without modification.
- **An open standard:** Like MCP, skills should be portable across tools and platforms. Use the `compatibility` field to note platform-specific requirements.

---

## Resources

- [This guide's source PDF](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Anthropic's complete guide
- [Public skills repository](https://github.com/anthropics/skills) — Anthropic-created examples
- [Claude Developers Discord](https://discord.gg/claudedev) — Community support
- [GitHub Issues: anthropic/skills/issues](https://github.com/anthropics/skills/issues) — Bug reports
- skill-creator skill — built into Claude.ai, use *"Help me build a skill using skill-creator"*
