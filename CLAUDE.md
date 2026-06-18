# NOT RED — Project Instructions

This project produces marketing content for **NOT RED**, a luxury/heirloom custom jewellery brand whose differentiator is symbolism.

## Sources of truth
- `BRAND.md` — the brand contract. Voice, visual rules, anti-brand. All agent output must comply.
- `collection/inventory.md` — the current pieces NOT RED has made or sells.
- `symbolism/` — research dossiers on motifs. Reused across campaigns.
- `reference/` — drop-zone for raw assets (photos, logo files, notes). Not version-controlled.

## The agent team

Four specialist subagents live in `.claude/agents/`:

| Agent | Purpose |
|---|---|
| `notred-brand-steward` | Owns `BRAND.md`. Final QA gate on every deliverable. |
| `notred-symbolism-researcher` | Produces motif dossiers grounded in verifiable sources. |
| `notred-copy-director` | Writes captions, web copy, lookbook essays in NOT RED's voice. |
| `notred-art-director` | Produces moodboard briefs, shot lists, image prompts. |

## Standard campaign flow

1. User writes a brief in `campaigns/<YYYY-Q#>-<name>/brief.md`.
2. `notred-symbolism-researcher` produces `symbolism/<motif>-dossier.md`.
3. `notred-copy-director` and `notred-art-director` work **in parallel** from the dossier.
4. `notred-brand-steward` reviews all drafts against `BRAND.md` and writes `campaigns/<name>/approval.md`.

## Rules
- No campaign work begins before the symbolism dossier exists.
- Agents output **text only**. They never generate images — they produce prompts for image-gen tools.
- The brand-steward is the only agent that approves. Others draft.
- If a claim about symbolism cannot be traced to a source, it does not ship.
