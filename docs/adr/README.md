# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records documenting significant technical decisions made in the Family Budget application.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## Format

Each ADR follows this structure:
- **Status**: Accepted/Superseded/Deprecated
- **Context**: The problem and requirements
- **Decision**: What was decided
- **Rationale**: Why this decision was made
- **Implementation**: Where and how it's implemented
- **Consequences**: Positive and negative outcomes
- **For AI Agents**: Specific guidance for implementing related features
- **References**: Links to relevant documentation

## Index of ADRs

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [001](001-pbkdf2-password-hashing.md) | PBKDF2 Password Hashing | Accepted | 2024-01-10 |
| [002](002-session-based-authentication.md) | Session-Based Authentication | Accepted | 2024-01-10 |
| [003](003-sqlite-database-choice.md) | SQLite Database Choice | Accepted | 2024-01-10 |
| [004](004-single-file-architecture.md) | Single-File Architecture | Accepted | 2024-01-10 |
| [005](005-jinja2-templating.md) | Jinja2 Templating | Accepted | 2024-01-10 |
| [006](006-tailwind-cdn-approach.md) | Tailwind CDN Approach | Accepted | 2024-01-10 |
| [007](007-demo-mode-design.md) | Demo Mode Design | Accepted | 2024-01-15 |

## When to Create a New ADR

Create an ADR when making a decision that:
- Has significant impact on the architecture
- Is difficult to reverse
- Affects multiple parts of the system
- Involves trade-offs between different approaches
- Future developers will need to understand

## Template

```markdown
---
type: adr
number: XXX
status: accepted
date: YYYY-MM-DD
---

# ADR-XXX: [Title]

## Status
[Accepted/Superseded/Deprecated]

## Context
[Describe the problem and requirements]

## Decision
[State the decision clearly]

## Rationale
[Explain why this decision was made]

## Implementation
[Where and how it's implemented in the codebase]

## Consequences

### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Trade-off 1]
- [Trade-off 2]

## For AI Agents
[Specific guidance for implementing features related to this decision]

## References
- [Link to relevant docs]
```

## Related Documentation

- **Code Patterns**: `../../PATTERNS.md` - How to implement these decisions
- **Implementation Guides**: `../guides/` - Step-by-step workflows
- **API Reference**: `../../src/API-REFERENCE.md` - Route documentation
