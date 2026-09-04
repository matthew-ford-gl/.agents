# Spawning Mechanism

Read this file at Phase 5 in `SKILL.md`, right before launching the three review agents.

Detect which runtime you are in and use its native mechanism for parallel agents:

- **Devin CLI**: spawn each agent with `run_subagent`, `profile: "subagent_general"`,
  `is_background: true` for all three agents, then collect each with `read_subagent`
  (`block: true`) once all three have been launched.
  - Read each agent's AGENT.md (resolved in Phase 4) and pass its full content as part
    of the task prompt, since the custom reviewer names may not be recognised built-in profiles.
  - **Profile fallback**: if a named profile is rejected as unrecognized, retry using
    `profile: "subagent_general"` with the agent's AGENT.md content in the prompt.
  - **Halt on failure**: if an agent fails to start even after the fallback attempt, STOP
    and tell the human which agent could not run and why.
- **Claude Code**: spawn each as an `Agent`/`Task` tool call with `subagent_type` set to
  the agent name and the complete Phase 5 persona plus review input as the prompt. If a
  custom type is unavailable despite its AGENT.md being resolved, use an unnamed/general
  agent with the same full prompt.
- **Other hosts**: use the native parallel-subagent primitive.

Launch all three simultaneously — do not wait for one to finish before starting the next.
