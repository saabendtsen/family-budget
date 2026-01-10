# Handoff: Family Budget Feature Implementation

> Opdateret: 2026-01-10
> Status: Alle P2 og P3 issues har PRs klar til review/merge

## Bemærk: Potentielle overlaps

Under denne session blev der oprettet GitHub issues #44-52 for features der tidligere kun fandtes i beads. Der kan være overlap med ældre GitHub issues:

| Nyt issue | Potentielt overlap med | Kommentar |
|-----------|------------------------|-----------|
| #45 (månedlig/årlig toggle) | #24 (Årsoverblik) | Forskellige features - #24 handler om visualisering, #45 om periode-toggle |
| #5 (CLOSED) | - | Quarterly/semi-annual frequencies - allerede implementeret |

**Beads er fjernet** - projektet bruger nu kun GitHub Issues.

---

## Færdige PRs (klar til merge)

### P2 Issues

| GitHub Issue | Titel | PR | Branch |
|--------------|-------|-----|--------|
| [#44](https://github.com/saabendtsen/family-budget/issues/44) | Tilføj udgift-knap direkte på kategori | [#35](https://github.com/saabendtsen/family-budget/pull/35) | `feature/add-expense-button-on-category` |
| [#45](https://github.com/saabendtsen/family-budget/issues/45) | Toggle månedlig/årlig visning på oversigt | [#36](https://github.com/saabendtsen/family-budget/pull/36) | `feature/monthly-yearly-toggle` |
| [#46](https://github.com/saabendtsen/family-budget/issues/46) | Vis sum af indkomst på indkomstsiden | [#37](https://github.com/saabendtsen/family-budget/pull/37) | `feature/income-sum-display` |
| [#47](https://github.com/saabendtsen/family-budget/issues/47) | Navigation fra oversigt til indkomst/udgift sider | [#38](https://github.com/saabendtsen/family-budget/pull/38) | `feature/dashboard-navigation` |

### P3 Issues

| GitHub Issue | Titel | PR | Branch |
|--------------|-------|-----|--------|
| [#48](https://github.com/saabendtsen/family-budget/issues/48) | GitHub link i hjælp-menuen | [#39](https://github.com/saabendtsen/family-budget/pull/39) | `feature/github-link-in-help` |
| [#49](https://github.com/saabendtsen/family-budget/issues/49) | Fold alle kategorier ind/ud på udgiftsiden | [#40](https://github.com/saabendtsen/family-budget/pull/40) | `feature/collapse-all-categories` |
| [#50](https://github.com/saabendtsen/family-budget/issues/50) | Sorteringsmuligheder for kategorier på oversigt | [#41](https://github.com/saabendtsen/family-budget/pull/41) | `feature/category-sorting-dashboard` |
| [#51](https://github.com/saabendtsen/family-budget/issues/51) | Fold kategorier ind/ud på oversigten | [#42](https://github.com/saabendtsen/family-budget/pull/42) | `feature/collapse-categories-dashboard` |
| [#52](https://github.com/saabendtsen/family-budget/issues/52) | Opret CI/CD pipeline | [#43](https://github.com/saabendtsen/family-budget/pull/43) | `feature/cicd-pipeline` |

---

## Øvrige åbne GitHub Issues (ikke behandlet i denne session)

| # | Titel | Prioritet |
|---|-------|-----------|
| 6 | Export data til Excel | Enhancement |
| 9 | Virtualisering (pie charts) | Enhancement |
| 20 | Frequency display text til help tooltip | UI |
| 22 | Feedback/kontakt-funktion | Enhancement |
| 23 | Note-felt til udgifter | Enhancement |
| 24 | Årsoverblik med månedlig fordeling | Enhancement |
| 26 | Flyt version/privacy ind i Help-menu | UI |
| 28 | Forbedret ikon-vælger til kategorier | UI |
| 29 | Bug: Version-nummer opdateres ikke | Bug |

---

## Næste skridt

1. Review og merge PRs #35-43
2. Konfigurer GitHub Secrets for deploy workflow (#43):
   - `DEPLOY_HOST`
   - `DEPLOY_USER`
   - `DEPLOY_SSH_KEY`
3. Prioriter øvrige åbne issues efter behov

## Commands

```bash
# List åbne issues
gh issue list

# List PRs
gh pr list

# Merge en PR
gh pr merge <nummer> --squash

# Cleanup branch efter merge
git branch -d <branch-name>
git push origin --delete <branch-name>
```
