---
type: adr
number: 006
status: accepted
date: 2024-01-10
---

# ADR-006: Tailwind CDN Approach

## Status
Accepted

## Context

Need CSS framework for styling. Options:
- TailwindCSS with build process (PostCSS, PurgeCSS)
- TailwindCSS CDN (no build)
- Bootstrap
- Custom CSS

## Decision

Use **TailwindCSS via CDN** (no build process).

## Rationale

### Why CDN

1. **No build step**: Just include script tag
2. **Simple deployment**: No Node.js required
3. **Fast development**: Change classes, refresh browser
4. **Good enough performance**: CDN is fast, file is cached
5. **All features available**: Full TailwindCSS utility classes

### Trade-offs

**Larger file size**: CDN includes all Tailwind classes (~100KB gzipped)
- **With build**: Could reduce to ~10KB with PurgeCSS
- **Decision**: 90KB savings not worth build complexity

**No customization**: Can't customize Tailwind config
- **Decision**: Default config covers 99% of needs
- **Alternative**: Can add custom CSS if needed

## Implementation

**Location**: `templates/base.html`

```html
<script src="https://cdn.tailwindcss.com"></script>
<script>
    tailwind.config = {
        theme: {
            extend: {
                colors: {
                    primary: '#10b981',  // Green
                }
            }
        }
    }
</script>
```

**Dark mode**: Using class strategy
```html
<html class="dark">  <!-- Toggle class for dark mode -->
```

## Consequences

### Positive
- Zero build configuration
- Fast development
- Simple deployment

### Negative
- Larger CSS bundle (100KB vs 10KB)
- No tree-shaking

**Acceptable**: Performance is good enough for this use case.

## For AI Agents

**Use Tailwind utility classes** for all styling:
```html
<button class="px-4 py-3 bg-primary text-white rounded-xl hover:bg-primary/90">
    Submit
</button>
```

**Always include dark mode variants**:
```html
<div class="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
    Content
</div>
```

See `../../PATTERNS.md` for standard class combinations.

## References
- Tailwind docs: https://tailwindcss.com/
- Pattern guide: `../../PATTERNS.md`
