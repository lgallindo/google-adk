# AGENTS.md — google-adk

Teaching repo for Google ADK agent variants (`00_conversa` … `09_pesquisa`).

## Prose we author

Follow the house rule **storytelling + no unnecessary negatives**
(`~/code/CLAUDE.md`, Cursor `storytelling-no-negatives.mdc`):

- Lead with the **razão de ser** of each folder or script.
- Prefer “é Y” over stacks of “não é X”.
- Keep each variant **self-contained** (prompts/data in the folder).
- Negation stays when it is the payload (errors, LLM constraints, log strings).

Applies to `README.md`, `*/agent.py` module docstrings, auxiliary modules
(`modelo.py`, `verificar.py`, `servico-local/`, `08_paralelo/pedidos.py`,
`cronometro.py`, `dados/baixar.py`, …). LLM `instruction=` strings may keep
behavioral forbids (“diga que não sabe”).
