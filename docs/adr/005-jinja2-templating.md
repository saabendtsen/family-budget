---
type: adr
number: 005
status: accepted
date: 2024-01-10
---

# ADR-005: Jinja2 Templating

## Status
Accepted

## Context

Need to render HTML pages for budget dashboard. Options:
- Server-side rendering (SSR) with templates
- Single-page application (SPA) with React/Vue
- Hybrid approach (htmx, Alpine.js)

## Decision

Use **Jinja2 templates** for server-side rendering with TailwindCSS (CDN).

## Rationale

### Why SSR with Jinja2

1. **Built into FastAPI**: No additional setup
2. **Simple deployment**: No build step required
3. **Good for content-heavy pages**: Dashboard shows lots of data
4. **SEO friendly**: Fully rendered HTML
5. **Fast initial load**: No large JavaScript bundles
6. **Works without JavaScript**: Core functionality doesn't require JS

### Why Not SPA

- **Overkill**: Budget app doesn't need complex client-side state
- **Build complexity**: Would need webpack/vite, babel, etc.
- **Deployment overhead**: Build step adds complexity
- **Slower initial load**: Need to download React/Vue bundle

### JavaScript Usage

Minimal JavaScript for:
- Modal open/close
- Form interactions
- Lucide icon initialization
- Chart rendering (if needed)

Located in `<script>` tags at bottom of templates.

## Implementation

**Template location**: `templates/`

**Base template**: `templates/base.html`
- Navigation
- Dark mode support
- TailwindCSS CDN
- Lucide icons CDN

**Pattern**: Template inheritance
```jinja2
{% extends "base.html" %}

{% block content %}
<div>Page content</div>
{% endblock %}
```

## Consequences

### Positive
- Simple to understand
- No build step
- Fast development
- Good performance

### Negative
- More server load (rendering HTML)
- Page refreshes on navigation

## For AI Agents

See `templates/CLAUDE.md` for template patterns and conventions.

## References
- Jinja2 docs: https://jinja.palletsprojects.com/
- Templates: `../../templates/`
