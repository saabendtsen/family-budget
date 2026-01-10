# Handoff: Family Budget Feature Implementation

> Oprettet: 2026-01-10
> Status: Issue 4s3 klar til implementation

## Workflow (som brugeren ønsker)

For hvert issue uden PR:
1. Spawn sub-agent sekventielt med `/feature-dev:feature-dev`
2. Hver arbejder på egen branch/worktree
3. Sub-agent laver plan med spørgsmål først → venter på bruger-svar
4. Når tests passer: commit, push, opret PR
5. Rapporter til main session
6. Main session vurderer og starter næste issue

## Current Status

### Issue 4s3 - IN PROGRESS
**Titel:** Tilføj udgift-knap direkte på kategori

**Worktree oprettet:**
```bash
~/projects/family-budget-4s3
Branch: feature/add-expense-button-on-category
```

**Brugerens beslutninger (bekræftet):**
- **Placering:** Plus-knap i kategori-headeren, til højre for totalen (før chevron)
- **Stil:** Diskret grå ikon der bliver blå ved hover
- Ved klik: Åbn tilføj-udgift modal med kategorien forudvalgt

**Kode-viden fra analyse:**
- `templates/expenses.html` - Udgiftssiden med kategorier i collapsible sektioner
- `openAddModal()` - Skal tilpasses til at acceptere optional category parameter
- Bruger Lucide icons og TailwindCSS

**Status:** Klar til implementation - brugerens spørgsmål er besvaret

---

## Remaining P2 Issues (prioriteret rækkefølge)

| ID | Beskrivelse |
|----|-------------|
| cpd | Toggle mellem månedlig og årlig visning på oversigt |
| eer | Vis sum af indkomst på indkomstsiden |
| 929 | Navigation fra oversigt til indkomst/udgift sider |
| ac3 | Add quarterly and semi-annual expense frequencies |

## P3 Issues

| ID | Beskrivelse |
|----|-------------|
| 1p9 | GitHub link i hjælp-menuen |
| wb0 | Fold alle kategorier ind/ud på udgiftsiden |
| 56g | Sorteringsmuligheder for kategorier på oversigt |
| nai | Fold kategorier ind/ud på oversigten |
| 0jf | Opret CI/CD pipeline til automatisk deployment |

## Commands til at fortsætte

```bash
# Check status
cd ~/projects/family-budget && bd ready

# Se issue detaljer
bd show family-budget-<id>

# Opret worktree for næste issue
git worktree add ../family-budget-<id> -b feature/<branch-name> origin/master

# List worktrees
git worktree list

# Cleanup worktree efter merge
git worktree remove ../family-budget-<id>
```

## Projekt-lokation
- Main repo: `~/projects/family-budget`
- Worktree for 4s3: `~/projects/family-budget-4s3`

## Næste skridt for 4s3

1. Åbn `~/projects/family-budget-4s3/templates/expenses.html`
2. Find kategori-header elementet (har chevron, kategorinavn, antal og total)
3. Tilføj plus-ikon mellem total og chevron
4. Modificer `openAddModal()` til at acceptere optional `categoryId` parameter
5. Tilføj click handler på plus-ikonet der kalder `openAddModal(categoryId)`
6. Test manuelt + kør eksisterende tests
7. Commit, push, opret PR
