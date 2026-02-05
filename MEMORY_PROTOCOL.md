# MEMORY PROTOCOL: CONTEXT INTEGRITY

> **Date**: 2026-02-05  
> **Type**: System Standard  
> **Status**: ACTIVE  

---

## 1. The "Memory Hole" Problem

AI Agents suffer from **Context Drift** (Trôi ngữ cảnh) over long conversations.
- **Turns 1-5**: High accuracy. Adheres to all rules.
- **Turns 10-15**: Tone relaxation. Minor rule skipping.
- **Turns 20+**: "Memory Hole". Complex constraints forgotten. Hallucination risk increases.

## 2. Protocol: Periodic Context Refresh

To maintain **Zero-Latency Accuracy**, EXECUTOR enforces a strict **Context Refresh** cycle.

**Rule:**
> Every **20 interactions**, the System Prompt MUST be re-injected.

This forces the AI to "remember" its core instructions, blocking the drift.

---

## 3. Configuration

Managed in `config/safety_limits.json`:

```json
{
  "memory": {
    "context_refresh_interval": 20,
    "max_conversation_history": 50,
    "force_system_prompt_reload": true
  }
}
```

## 4. Operational Logic

1. **Count**: Orchestrator tracks `interaction_count` for each active agent.
2. **Check**: Before processing a task/reply, check `if count >= interval`.
3. **Execute**:
   - Log: `♻️ CONTEXT REFRESH: Agent [ID] reached 20 turns.`
   - Action: Reload `system_prompt` from `SkillInjector`.
   - Action: Truncate conversation history (keep last N messages + System Prompt).
4. **Reset**: `interaction_count = 0`.

## 5. Violation Consequences

If this protocol is disabled:
- Agents WILL deviate from "Beast Mode".
- Strict rules (e.g., "No placeholders") WILL be ignored.
- System integrity reaches CRITICAL risk after 30 turns.

**DO NOT DISABLE.**
