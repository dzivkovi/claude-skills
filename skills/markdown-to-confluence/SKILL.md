---
name: markdown-to-confluence
description: "Draft or update a Confluence Cloud page from a Markdown file, with Mermaid diagrams rendered locally to PNG so they display as pictures instead of as code. Use when the user wants a Markdown doc pushed to Confluence, a wiki page drafted from a repo document, an existing page refreshed from its Markdown source, or diagrams that show up properly in Confluence. Triggers: 'put this on Confluence', 'draft a Confluence page from this', 'publish this to the wiki', 'update that Confluence page', 'my architecture doc needs to go on Confluence', 'the mermaid diagrams show as code in Confluence'. Sibling of markdown-to-pdf (print) and markdown-to-epub (e-reader); this one targets a wiki page. NOT for Jira issues, and NOT for reading Confluence, both of which the Atlassian MCP already does directly."
metadata:
  version: 0.1.0
---

# markdown-to-confluence

Turn a Markdown file into a Confluence Cloud page, with ```mermaid fences rendered locally so they arrive as diagrams rather than as a wall of source, and with existing local image references resolved so they arrive as pictures rather than as dead links. Sibling of `markdown-to-pdf` (print-grade PDF) and `markdown-to-epub` (e-reader); all three render Mermaid through the same local `mmdc` step and differ only in what they do with the result.

## Step 0 - the hard dependency

**This skill does nothing without the Atlassian MCP server connected and authenticated for the target site.** Publishing happens through its `createConfluencePage` and `updateConfluencePage` tools; there is no REST fallback in this skill.

Check for `mcp__atlassian__*` tools before starting. If they are absent, stop and tell the user to connect and authorize the Atlassian MCP via `claude mcp` or `/mcp` **in an interactive session**. An agent cannot complete the OAuth flow itself, so there is no way to work around this from inside a task.

`mmdc` is needed only when the document contains mermaid fences: `npm install -g @mermaid-js/mermaid-cli`. Documents without diagrams never invoke it. The preparation script itself has no Python dependencies beyond the standard library.

## Step 1 - what the MCP already handles, and the one thing it does not

The Atlassian MCP accepts `contentFormat: "markdown"` and converts the body to native Confluence storage format on its own. Verified against a live Confluence Cloud site:

| Markdown | Becomes | Verdict |
| --- | --- | --- |
| Headings, bold, italic, inline code, links | The same elements | Clean |
| Pipe tables | A native Confluence table, header row preserved | Clean |
| Fenced code with a language | A native code macro with the language set | Clean |
| Lists, blockquotes | The same elements | Clean |
| `![alt](data:image/png;base64,...)` | A Confluence image node, rendered at full size | Works |
| `![alt](docs/diagram.png)` (a path that exists on disk) | Sent to Confluence as literal text; there is no filesystem for it to resolve against | **Broken - the gap this skill also closes** |
| ` ```mermaid ` fence | **A code macro showing the mermaid source, not a diagram** | The gap this skill closes |

So do not reach for pandoc, do not convert to HTML, and do not strip attributes. Send Markdown. The preprocessing that earns its place is rendering the Mermaid fences, resolving local image references against the source file, and lifting the leading H1 out because the page title is a separate argument.

## Step 2 - prepare the body

```bash
uv run scripts/prepare_confluence_markdown.py <source.md> --images placeholders
```

The script renders every Mermaid fence to PNG, resolves existing local image references, substitutes an image reference for each, lifts the leading H1 out as the title, and prints the title, the body size, and the PNG and image filenames.

**Choose the image mode deliberately. It is the one real tradeoff in this skill.** The same mode governs rendered diagrams and existing local images, so a document that mixes both reads consistently either way.

| Mode | Body size | What it costs |
| --- | --- | --- |
| `--images inline` | Grows by about 1.35x the image bytes | Nothing manual, but every byte crosses the MCP tool call and therefore the agent's context, at roughly a token per four bytes. The script warns above 60 KB. |
| `--images placeholders` | Smallest by far | Each diagram or local image becomes a one-line blockquote naming its file, which the author drags into the editor afterwards. |
| `--images files` | Small | Plain filename references, for a pipeline that uploads the images as attachments over the REST API. |

A three-diagram architecture document measured 128 KB inline against 9 KB with placeholders. Prefer `inline` for one or two small images or when the page must arrive complete in a single pass; prefer `placeholders` for anything larger.

**The PNGs are written to disk in every mode, including `inline`.** They are always available as a fallback, which matters for the cross-instance workflow below.

**Local image references are resolved against the source file's own directory, not the output directory or the working directory.** `![alt](docs/diagram.png)` inside `notes/page.md` looks for `notes/docs/diagram.png`. `http://`, `https://`, and `data:` sources are left completely untouched, since they already work in a page body without help. Angle-bracket destinations (`![alt](<path with spaces.png>)`, with or without a trailing `"title"`) are supported, because that syntax exists precisely to let a path contain spaces, and are normalized to the plain form either way so an angle-bracket destination cannot corrupt the rendered page. When a referenced file cannot be resolved, the script does not fail the run: it prints a warning naming the unresolved path, leaves a plain (non-angle-bracket) reference in the body so the page still opens cleanly, and counts it as unresolved in the stdout report rather than the resolved count. In `placeholders` and `files` modes, resolved local images are copied next to the output file alongside the rendered PNGs, ready to drag in; `inline` mode embeds them as data URIs and copies nothing.

## Step 3 - publish

Resolve the target before writing anything:

1. `mcp__atlassian__getAccessibleAtlassianResources` gives the `cloudId`.
2. `mcp__atlassian__getConfluenceSpaces` gives spaces. A space key or personal-space key is accepted wherever a numeric `spaceId` is asked for.
3. **If the user keeps pages under a parent page** (a per-project or per-engagement folder, which is a common way to organize a space), find that parent's page id with `mcp__atlassian__getPagesInConfluenceSpace` or `searchConfluenceUsingCql`, and pass it as `parentId`. **Ask the user for the parent's name or URL rather than assuming one.** Never hardcode a parent, a space, or a site into this skill.

Then `createConfluencePage` (new) or `updateConfluencePage` (existing, needs `pageId`), with `contentFormat: "markdown"`, the title from step 2, and `status: "draft"` unless the user asked to publish.

Report the page URL from `_links.webui`, prefixed with `_links.base`. When placeholders were used, list the PNG and image paths still to be dragged in.

## Limitations worth stating before someone hits them

**A draft cannot be flipped to published by updating it.** Confluence rejects it: "Version number must be 1 when publishing a page for the first time." Decide draft or published at creation. To publish an existing draft, create a new page with `status: "current"`.

**The MCP cannot upload attachments.** Its OAuth scopes cover pages, spaces, search, and comments, with nothing for attachments. Real attachment upload needs a multipart POST to `/rest/api/content/{pageId}/child/attachment` with an `X-Atlassian-Token: no-check` header and an API token. That is why `placeholders` is a first-class mode rather than a workaround: a drag-and-drop in the editor beats provisioning a token until volume justifies it.

**Data URI images are stored as URL references, not attachments.** They render correctly, but they live inside the page body, so they inflate the body and the editor rather than sitting in the attachment store.

**Escape nothing.** Pass raw Markdown in the `body` argument. HTML-escaping it produces a page containing the literal markup as visible text. This is an easy mistake to make when the body travels through a tool call.

**Confluence normalizes some code languages.** `bash` comes back as `shell`. Harmless; do not treat it as a failure.

## Confluence Data Center and Server (self-hosted)

**This skill targets Confluence Cloud only.** Self-hosted Confluence runs a different API version, different auth, and stores pages as storage format rather than the format the MCP speaks. There is no MCP path to it.

The workable pattern for a self-hosted destination is to draft on a Cloud instance with this skill, open the destination page in **edit mode**, and paste the rendered body across. Confluence-to-Confluence paste carries headings, tables, code blocks, and images as one body of text, and the destination editor re-uploads pasted images as its own attachments. Older self-hosted versions are the ones most likely to drop an embedded `data:` URI on paste or save, which is the same class of problem as embedded video on older versions. If a pasted diagram does not survive, the rendered PNGs are already on disk from step 2: drag them in.

## Sibling skills

`markdown-to-pdf` prints the same source as a working document. `markdown-to-epub` targets e-readers. A Mermaid diagram that renders in one renders in all three, because they share the same local `mmdc` step.
