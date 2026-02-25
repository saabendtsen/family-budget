# Install Guide Design

**Issue:** #105 — How to install as app
**Date:** 2026-02-25
**Status:** Approved

## Summary

Add a minimal PWA manifest and an in-app modal guide that explains how to install the family-budget app on iOS and Android. The modal component is also saved as a reusable template.

## Scope

**In scope:**
- `manifest.json` served via FastAPI static files
- App icons (192×192 and 512×512 PNG)
- In-app modal with iOS/Android tabs and step-by-step instructions
- Trigger button in navbar
- Reusable template in `~/templates/install-guide/`

**Out of scope:**
- Service worker / offline caching
- Push notifications
- Desktop install flow

## Architecture

### 1. manifest.json

Minimal PWA manifest linked in base HTML template:

```json
{
  "name": "Family Budget",
  "short_name": "Budget",
  "start_url": "/budget/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2563eb",
  "icons": [
    { "src": "/budget/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/budget/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

Served at: `/budget/static/manifest.json`
Linked in base template: `<link rel="manifest" href="/budget/static/manifest.json">`

### 2. App Icons

Two PNG icons generated from app design:
- `src/static/icons/icon-192.png`
- `src/static/icons/icon-512.png`

### 3. InstallGuideModal

Jinja2/HTML + Tailwind CSS modal component:

- **Trigger:** "Installer app" link with Lucide `download` icon in navbar
- **Tabs:** iOS and Android, auto-selected based on `navigator.userAgent`
- **iOS tab steps:**
  1. Åbn appen i Safari (ikke Chrome)
  2. Tryk på Del-ikonet (firkant med pil op)
  3. Rul ned og tryk "Føj til hjemmeskærm"
  4. Tryk "Tilføj"
- **Android tab steps:**
  1. Åbn appen i Chrome
  2. Tryk på ⋮ menuen øverst til højre
  3. Tryk "Tilføj til startskærm"
  4. Tryk "Installer"
- **Dismiss:** ✕ button or click outside modal

**Platform detection (JavaScript):**
```js
const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
const isAndroid = /Android/.test(navigator.userAgent);
// Default to iOS tab on desktop
```

### 4. Navbar Trigger

Adds a discrete "Installer app" link to the existing navbar. Uses Lucide `download` icon consistent with existing icon usage.

## Template Structure

```
~/templates/install-guide/
├── modal.html              # Standalone copy-paste modal component
├── manifest.template.json  # Manifest with placeholders (APP_NAME, START_URL, THEME_COLOR)
└── README.md               # Usage instructions for other projects
```

## Files Changed

| File | Action |
|------|--------|
| `src/static/manifest.json` | Create |
| `src/static/icons/icon-192.png` | Create |
| `src/static/icons/icon-512.png` | Create |
| `src/templates/base.html` | Add manifest link tag |
| `src/templates/components/install_guide_modal.html` | Create |
| `src/templates/base.html` | Include modal + trigger button in navbar |
| `~/templates/install-guide/modal.html` | Create (template copy) |
| `~/templates/install-guide/manifest.template.json` | Create |
| `~/templates/install-guide/README.md` | Create |
