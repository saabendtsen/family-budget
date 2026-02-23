# Design: Årsoverblik med månedlig fordeling

**Issue:** [#24](https://github.com/saabendtsen/family-budget/issues/24)
**Dato:** 2026-02-23
**Motivation:** Likviditetsplanlægning — vide hvilke måneder der er dyre

## Beslutninger

| Beslutning | Valg |
|---|---|
| Placering | Ny separat side (`/budget/yearly`), dashboard uændret |
| Scope | Kun udgifter (ikke indkomst) får månedsvælger |
| Datamodel | JSON-kolonne `months TEXT` på expenses |
| Validering | Antal valgte måneder skal matche frekvens |
| Årsoverblik UI | 12-kolonne tabel med kategorier som rækker |
| Månedsvælger placering | Under "Avanceret" i expense-modalen |

## Datamodel

```sql
ALTER TABLE expenses ADD COLUMN months TEXT;
-- NULL = fordeles ligeligt (backwards compatible)
-- JSON array: [3, 9] = marts + september
```

**Expense dataclass:**
- Nyt felt: `months: list[int] | None = None`
- Ny metode: `get_monthly_amounts() -> dict[int, float]`
  - `months = None` → fordel ligeligt baseret på frekvens
  - `months = [3, 9]` → fordel beløbet over de valgte måneder

**Validering:**
- Månedlig → ingen månedsvælger (per definition hver måned)
- Kvartalsvis → præcis 4 måneder
- Halvårlig → præcis 2 måneder
- Årlig → præcis 1 måned
- Værdier skal være integers 1-12

## Frontend: Månedsvælger

**Placering:** I "Avanceret"-sektionen i expense-modalen. Kun synlig for ikke-månedlige frekvenser.

**UI:**
- 12 toggle-buttons i 6x2 grid (mobil: 4x3)
- Danske forkortelser: Jan, Feb, Mar, Apr, Maj, Jun, Jul, Aug, Sep, Okt, Nov, Dec
- Valgt = filled/primary, ikke-valgt = outline/grå
- Info-tekst: "Vælg [N] måneder" + "Ikke valgt = fordeles ligeligt"

**Interaktion:**
- Klik toggler måned on/off
- Når krævede antal er valgt, disables øvrige (kan stadig fjerne valgte)
- Frekvensændring nulstiller månedsvælger
- Gemmes som del af expense POST/PUT

## Frontend: Årsoverblik-side

**Route:** `GET /budget/yearly`
**Navigation:** Nyt menupunkt "Årsoverblik" i sidebar

**Tabel:**
```
                Jan     Feb     Mar    ...    Dec    År total
─────────────────────────────────────────────────────────────
Bolig          5.000   5.000   5.000        5.000    60.000
Transport        500     500   3.500          500    10.000
Forsikring         0       0   3.000            0     6.000
─────────────────────────────────────────────────────────────
Udgifter i alt 12.000  11.500  15.000       13.000  156.000
Indkomst       25.000  25.000  25.000       25.000  300.000
─────────────────────────────────────────────────────────────
Balance        13.000  13.500  10.000       12.000  144.000
```

- Rækker grupperet per kategori
- Indkomst fordeles ligeligt (ingen månedsvælger for income)
- Balance farvekodet: grøn/rød
- Beløb med dansk tusindtal-formatering
- Responsive: mobil har horisontal scroll med sticky kategori-kolonne

## Edge Cases

- Ingen udgifter med månedstilknytning → alt fordeles ligeligt
- Frekvensændring → months nulstilles
- Expense slettet → ingen orphan data (months er på expense-rækken)
- Ingen breaking changes: dashboard, eksisterende expenses og tests uændret

## Testing

**Unit tests:**
- `get_monthly_amounts()` for alle frekvenser og month-kombinationer
- Validering af months-felt (korrekt antal, gyldige værdier)
- Database migration

**E2E tests (Playwright):**
- Opret expense med månedsvælger → verificér den gemmes
- Redigér expense → verificér måneder vises korrekt
- Årsoverblik viser korrekte beløb per måned
- Expense uden måneder → fordeles ligeligt i årsoverblik
