# Install Guide Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a minimal PWA manifest and an in-app install guide modal (iOS + Android) to family-budget, plus save the modal as a reusable template.

**Architecture:** Static files are mounted via FastAPI's `StaticFiles` at `/budget/static`. A `manifest.json` links the app's icons and metadata. An HTML modal component handles the install guide, triggered from the "Om" page.

**Tech Stack:** FastAPI, Jinja2, Tailwind CSS (CDN), Lucide icons, ImageMagick (`convert`), vanilla JS

---

### Task 1: Add static file serving

**Files:**
- Modify: `src/api.py` (after `app = FastAPI(...)` block, around line 175)
- Create: `static/` directory at project root

**Step 1: Create the static directory**

```bash
mkdir -p ~/projects/family-budget/static/icons
```

**Step 2: Add StaticFiles mount to `src/api.py`**

Add import at top (near existing fastapi imports, line ~21):
```python
from fastapi.staticfiles import StaticFiles
```

Add mount after the middleware lines (after line ~180):
```python
# Serve static files
STATIC_DIR = Path(__file__).parent.parent / "static"
app.mount("/budget/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
```

**Step 3: Write a failing test**

In `tests/test_api.py`, add to the `TestAuthentication` class (or a new class at end of file):

```python
class TestStaticFiles:
    """Tests for static file serving."""

    def test_manifest_json_accessible(self, client):
        """manifest.json should be served at /budget/static/manifest.json."""
        response = client.get("/budget/static/manifest.json")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
```

**Step 4: Run test to verify it fails**

```bash
cd ~/projects/family-budget && venv/bin/pytest tests/test_api.py::TestStaticFiles -v
```
Expected: FAIL — manifest.json doesn't exist yet (404)

**Step 5: Verify the server starts with the mount**

```bash
cd ~/projects/family-budget && venv/bin/python -c "from src.api import app; print('OK')"
```
Expected: `OK` (no import errors)

**Step 6: Commit**

```bash
cd ~/projects/family-budget
git checkout -b feat/install-guide
git add src/api.py static/
git commit -m "feat: mount static files at /budget/static"
```

---

### Task 2: Generate app icons and manifest.json

**Files:**
- Create: `static/manifest.json`
- Create: `static/icons/icon-192.png`
- Create: `static/icons/icon-512.png`

**Step 1: Generate icons with ImageMagick**

Creates a blue rounded square with white "B" — matches the app's primary blue (`#3b82f6`):

```bash
# 192×192 icon
convert -size 192x192 xc:'#3b82f6' \
  -fill white -font DejaVu-Sans-Bold -pointsize 96 \
  -gravity Center -annotate 0 "B" \
  ~/projects/family-budget/static/icons/icon-192.png

# 512×512 icon
convert -size 512x512 xc:'#3b82f6' \
  -fill white -font DejaVu-Sans-Bold -pointsize 256 \
  -gravity Center -annotate 0 "B" \
  ~/projects/family-budget/static/icons/icon-512.png
```

**Step 2: Create `static/manifest.json`**

```json
{
  "name": "Family Budget",
  "short_name": "Budget",
  "description": "Hold styr på familiens økonomi",
  "start_url": "/budget/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#3b82f6",
  "icons": [
    {
      "src": "/budget/static/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/budget/static/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

**Step 3: Run the failing test from Task 1**

```bash
cd ~/projects/family-budget && venv/bin/pytest tests/test_api.py::TestStaticFiles -v
```
Expected: PASS — manifest.json is now served

**Step 4: Add icon tests**

```python
def test_icon_192_accessible(self, client):
    response = client.get("/budget/static/icons/icon-192.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

def test_icon_512_accessible(self, client):
    response = client.get("/budget/static/icons/icon-512.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
```

**Step 5: Run all static tests**

```bash
cd ~/projects/family-budget && venv/bin/pytest tests/test_api.py::TestStaticFiles -v
```
Expected: All 3 PASS

**Step 6: Commit**

```bash
cd ~/projects/family-budget
git add static/
git commit -m "feat: add PWA manifest and app icons"
```

---

### Task 3: Link manifest in base.html

**Files:**
- Modify: `templates/base.html` (in `<head>`, after line 5)

**Step 1: Add manifest and theme-color meta tags**

In `templates/base.html`, add after the `<meta name="viewport" ...>` line (line 5):

```html
    <link rel="manifest" href="/budget/static/manifest.json">
    <meta name="theme-color" content="#3b82f6">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Budget">
    <link rel="apple-touch-icon" href="/budget/static/icons/icon-192.png">
```

Note: `apple-touch-icon` is required for iOS home screen icon — Safari ignores `manifest.json` for icons.

**Step 2: Write failing test**

In `tests/test_api.py`, add to `TestAuthentication` or a suitable class:

```python
def test_base_html_links_manifest(self, client):
    """All pages should include manifest link."""
    response = client.get("/budget/login")
    assert response.status_code == 200
    assert 'rel="manifest"' in response.text
    assert '/budget/static/manifest.json' in response.text
```

**Step 3: Run test to verify it fails**

```bash
cd ~/projects/family-budget && venv/bin/pytest tests/test_api.py -k "test_base_html_links_manifest" -v
```
Expected: FAIL

**Step 4: Apply the edit to `templates/base.html`**

(See step 1 above for exact HTML to insert)

**Step 5: Run test to verify it passes**

```bash
cd ~/projects/family-budget && venv/bin/pytest tests/test_api.py -k "test_base_html_links_manifest" -v
```
Expected: PASS

**Step 6: Commit**

```bash
cd ~/projects/family-budget
git add templates/base.html tests/test_api.py
git commit -m "feat: link PWA manifest in base template"
```

---

### Task 4: Create install guide modal component

**Files:**
- Create: `templates/components/install_guide_modal.html`

**Step 1: Create the components directory and modal file**

Create `templates/components/install_guide_modal.html`:

```html
<!-- Install Guide Modal -->
<!-- Trigger: set window.openInstallGuide = true or call openInstallGuide() -->
<div id="install-guide-modal"
     class="fixed inset-0 z-50 flex items-end sm:items-center justify-center hidden"
     role="dialog" aria-modal="true" aria-labelledby="install-guide-title">

  <!-- Backdrop -->
  <div id="install-guide-backdrop"
       class="absolute inset-0 bg-black/50"
       onclick="closeInstallGuide()"></div>

  <!-- Modal panel -->
  <div class="relative w-full sm:max-w-md bg-white dark:bg-gray-800 rounded-t-2xl sm:rounded-2xl shadow-xl p-6 z-10">

    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h2 id="install-guide-title" class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <i data-lucide="smartphone" class="w-5 h-5 text-primary"></i>
        Installer som app
      </h2>
      <button onclick="closeInstallGuide()"
              class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1 rounded-lg"
              aria-label="Luk">
        <i data-lucide="x" class="w-5 h-5"></i>
      </button>
    </div>

    <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
      Tilføj Budget til din startskærm og brug den som en rigtig app — uden adresselinje.
    </p>

    <!-- Platform tabs -->
    <div class="flex rounded-lg bg-gray-100 dark:bg-gray-700 p-1 mb-5" role="tablist">
      <button id="tab-ios"
              onclick="switchTab('ios')"
              role="tab"
              class="flex-1 text-sm font-medium py-1.5 rounded-md transition-colors"
              aria-selected="true">
        iOS (Safari)
      </button>
      <button id="tab-android"
              onclick="switchTab('android')"
              role="tab"
              class="flex-1 text-sm font-medium py-1.5 rounded-md transition-colors"
              aria-selected="false">
        Android (Chrome)
      </button>
    </div>

    <!-- iOS steps -->
    <ol id="steps-ios" class="space-y-3 text-sm text-gray-700 dark:text-gray-300">
      <li class="flex items-start gap-3">
        <span class="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/40 text-primary text-xs font-bold flex items-center justify-center">1</span>
        <span>Åbn appen i <strong>Safari</strong> (ikke Chrome eller Firefox)</span>
      </li>
      <li class="flex items-start gap-3">
        <span class="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/40 text-primary text-xs font-bold flex items-center justify-center">2</span>
        <span>Tryk på <strong>Del-ikonet</strong> nederst på skærmen (firkant med pil op ↑)</span>
      </li>
      <li class="flex items-start gap-3">
        <span class="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/40 text-primary text-xs font-bold flex items-center justify-center">3</span>
        <span>Rul ned i menuen og tryk <strong>"Føj til hjemmeskærm"</strong></span>
      </li>
      <li class="flex items-start gap-3">
        <span class="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/40 text-primary text-xs font-bold flex items-center justify-center">4</span>
        <span>Tryk <strong>"Tilføj"</strong> øverst til højre</span>
      </li>
    </ol>

    <!-- Android steps -->
    <ol id="steps-android" class="space-y-3 text-sm text-gray-700 dark:text-gray-300 hidden">
      <li class="flex items-start gap-3">
        <span class="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/40 text-primary text-xs font-bold flex items-center justify-center">1</span>
        <span>Åbn appen i <strong>Chrome</strong></span>
      </li>
      <li class="flex items-start gap-3">
        <span class="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/40 text-primary text-xs font-bold flex items-center justify-center">2</span>
        <span>Tryk på <strong>⋮ menuen</strong> øverst til højre</span>
      </li>
      <li class="flex items-start gap-3">
        <span class="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/40 text-primary text-xs font-bold flex items-center justify-center">3</span>
        <span>Tryk <strong>"Tilføj til startskærm"</strong> eller <strong>"Installer app"</strong></span>
      </li>
      <li class="flex items-start gap-3">
        <span class="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/40 text-primary text-xs font-bold flex items-center justify-center">4</span>
        <span>Tryk <strong>"Installer"</strong> i den dialog der vises</span>
      </li>
    </ol>

  </div>
</div>

<script>
  (function() {
    function getActiveTabClass() {
      return 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm';
    }
    function getInactiveTabClass() {
      return 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200';
    }

    window.openInstallGuide = function() {
      const modal = document.getElementById('install-guide-modal');
      modal.classList.remove('hidden');
      // Auto-select platform tab
      const isAndroid = /Android/i.test(navigator.userAgent);
      switchTab(isAndroid ? 'android' : 'ios');
      lucide.createIcons();
    };

    window.closeInstallGuide = function() {
      document.getElementById('install-guide-modal').classList.add('hidden');
    };

    window.switchTab = function(platform) {
      const iosTab = document.getElementById('tab-ios');
      const androidTab = document.getElementById('tab-android');
      const iosSteps = document.getElementById('steps-ios');
      const androidSteps = document.getElementById('steps-android');
      const active = getActiveTabClass();
      const inactive = getInactiveTabClass();

      if (platform === 'ios') {
        iosTab.className = 'flex-1 text-sm font-medium py-1.5 rounded-md transition-colors ' + active;
        androidTab.className = 'flex-1 text-sm font-medium py-1.5 rounded-md transition-colors ' + inactive;
        iosTab.setAttribute('aria-selected', 'true');
        androidTab.setAttribute('aria-selected', 'false');
        iosSteps.classList.remove('hidden');
        androidSteps.classList.add('hidden');
      } else {
        androidTab.className = 'flex-1 text-sm font-medium py-1.5 rounded-md transition-colors ' + active;
        iosTab.className = 'flex-1 text-sm font-medium py-1.5 rounded-md transition-colors ' + inactive;
        androidTab.setAttribute('aria-selected', 'true');
        iosTab.setAttribute('aria-selected', 'false');
        androidSteps.classList.remove('hidden');
        iosSteps.classList.add('hidden');
      }
    };

    // Close on Escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') closeInstallGuide();
    });
  })();
</script>
```

**Step 2: Include modal in `templates/base.html`**

Add just before `{% block scripts %}{% endblock %}` (line 302):

```html
    {% include "components/install_guide_modal.html" %}
```

**Step 3: Write test**

```python
def test_install_modal_in_base(self, client):
    """Install guide modal should be present on all pages."""
    response = client.get("/budget/login")
    assert response.status_code == 200
    assert 'install-guide-modal' in response.text
    assert 'openInstallGuide' in response.text
```

**Step 4: Run test to verify it fails**

```bash
cd ~/projects/family-budget && venv/bin/pytest tests/test_api.py -k "test_install_modal_in_base" -v
```
Expected: FAIL

**Step 5: Apply changes (create modal file + add include to base.html)**

**Step 6: Run test to verify it passes**

```bash
cd ~/projects/family-budget && venv/bin/pytest tests/test_api.py -k "test_install_modal" -v
```
Expected: PASS

**Step 7: Run full test suite to check for regressions**

```bash
cd ~/projects/family-budget && venv/bin/pytest tests/ -v --tb=short
```
Expected: All existing tests pass

**Step 8: Commit**

```bash
cd ~/projects/family-budget
git add templates/components/install_guide_modal.html templates/base.html tests/test_api.py
git commit -m "feat: add install guide modal component"
```

---

### Task 5: Add trigger button to Om page

**Files:**
- Modify: `templates/om.html`

**Step 1: Add install guide section to `templates/om.html`**

After the `<!-- Kom i gang -->` section (around line 37), add a new section:

```html
        <!-- Installer som app -->
        <section class="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                <i data-lucide="smartphone" class="w-5 h-5 mr-2 text-primary"></i>
                Installer som app
            </h2>
            <p class="text-sm text-gray-600 dark:text-gray-300 mb-3">
                Tilføj Budget til din startskærm og brug den som en rigtig app — uden adresselinje og browser-UI.
            </p>
            <button onclick="openInstallGuide()"
                    class="flex items-center gap-2 text-sm font-medium text-primary hover:text-blue-700 dark:hover:text-blue-300 transition-colors">
                <i data-lucide="download" class="w-4 h-4"></i>
                Vis installationsvejledning
            </button>
        </section>
```

**Step 2: Write test**

```python
def test_om_page_has_install_button(self, authenticated_client):
    """Om page should have install guide trigger."""
    response = authenticated_client.get("/budget/om")
    assert response.status_code == 200
    assert 'openInstallGuide()' in response.text
    assert 'Installer som app' in response.text
```

**Step 3: Run test to verify it fails**

```bash
cd ~/projects/family-budget && venv/bin/pytest tests/test_api.py -k "test_om_page_has_install_button" -v
```
Expected: FAIL

**Step 4: Apply the edit to `templates/om.html`**

**Step 5: Run test to verify it passes**

```bash
cd ~/projects/family-budget && venv/bin/pytest tests/test_api.py -k "test_om_page_has_install_button" -v
```
Expected: PASS

**Step 6: Commit**

```bash
cd ~/projects/family-budget
git add templates/om.html tests/test_api.py
git commit -m "feat: add install guide trigger to Om page"
```

---

### Task 6: Create reusable template

**Files:**
- Create: `~/templates/install-guide/modal.html`
- Create: `~/templates/install-guide/manifest.template.json`
- Create: `~/templates/install-guide/README.md`

**Step 1: Create template directory**

```bash
mkdir -p ~/templates/install-guide
```

**Step 2: Create `~/templates/install-guide/modal.html`**

Copy the modal from `templates/components/install_guide_modal.html` and replace app-specific values with placeholders:

- Replace `"Installer som app"` headings with `"Installer {{ APP_NAME }} som app"`
- Add comment at top: `{# Template: install-guide/modal.html — Copy to templates/components/install_guide_modal.html #}`
- Keep all JS and Tailwind classes as-is (they are generic)

The file should be identical to the family-budget version except `APP_NAME` is a Jinja2 variable instead of hardcoded "Budget".

**Step 3: Create `~/templates/install-guide/manifest.template.json`**

```json
{
  "name": "APP_NAME",
  "short_name": "APP_SHORT_NAME",
  "description": "APP_DESCRIPTION",
  "start_url": "APP_START_URL",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "APP_THEME_COLOR",
  "icons": [
    {
      "src": "APP_STATIC_PREFIX/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "APP_STATIC_PREFIX/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

**Step 4: Create `~/templates/install-guide/README.md`**

```markdown
# Install Guide Template

Reusable in-app install guide modal for Progressive Web Apps.

## Files

- `modal.html` — Jinja2/HTML modal component. Include in your base template.
- `manifest.template.json` — PWA manifest template. Replace placeholders before use.

## Usage

### 1. Copy and configure manifest

Copy `manifest.template.json` to `static/manifest.json` and replace all `APP_*` placeholders.

### 2. Mount static files (FastAPI)

```python
from fastapi.staticfiles import StaticFiles
app.mount("/prefix/static", StaticFiles(directory="static"), name="static")
```

### 3. Include modal in base template

```html
{% include "components/install_guide_modal.html" %}
```

### 4. Add trigger button

```html
<button onclick="openInstallGuide()">Installer som app</button>
```

### 5. Link manifest in `<head>`

```html
<link rel="manifest" href="/prefix/static/manifest.json">
<meta name="theme-color" content="#3b82f6">
<meta name="apple-mobile-web-app-capable" content="yes">
<link rel="apple-touch-icon" href="/prefix/static/icons/icon-192.png">
```

## Notes

- iOS: Safari always requires manual "Add to Home Screen" — there is no automatic prompt.
- Android: Chrome shows a native install banner automatically when a valid manifest is present.
- Icons: Generate 192×192 and 512×512 PNG icons. ImageMagick example:
  `convert -size 192x192 xc:'#3b82f6' -fill white -gravity Center -annotate 0 "B" icon-192.png`
```

**Step 5: Commit template files**

```bash
cd ~/templates
git add install-guide/
git commit -m "feat: add install-guide modal template"
git push
```

---

### Task 7: Final verification

**Step 1: Run full test suite**

```bash
cd ~/projects/family-budget && venv/bin/pytest tests/ -v --tb=short
```
Expected: All tests pass

**Step 2: Run E2E smoke test (optional)**

```bash
cd ~/projects/family-budget && venv/bin/pytest e2e/ -v -k "test_login" --tb=short
```

**Step 3: Push branch and create PR**

```bash
cd ~/projects/family-budget
git push -u origin feat/install-guide
gh pr create \
  --title "feat: add PWA manifest and install guide modal (fixes #105)" \
  --body "## Summary
- Adds \`manifest.json\` + app icons served via FastAPI static files
- Adds install guide modal with iOS and Android tabs (auto-detects platform)
- Adds trigger section to 'Om' page
- Saves reusable template to \`~/templates/install-guide/\`

Fixes #105" \
  --base master
```
