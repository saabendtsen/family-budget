# Privacy Policy Research - Family Budget

## TL;DR

**Du behøver IKKE en cookie consent pop-up** fordi:
- Session cookies til authentication er "strictly necessary" og dermed undtaget
- Ingen tredjepartstræckere eller analytics
- Ingen marketing cookies

**Du SKAL stadig have:**
- En Privacy Policy side (kan være simpel)
- Transparens om hvilke data du gemmer

---

## Juridisk Baggrund

### GDPR + ePrivacy Directive

Cookie consent krav stammer fra to love:
1. **GDPR** - Generel databeskyttelse
2. **ePrivacy Directive** (Cookie Law) - Specifikt om cookies

### Strictly Necessary Cookies = Undtaget

> "Strictly necessary cookies are exempt from the consent requirements of privacy laws, such as the GDPR and the ePrivacy Directive."
> — [CookieYes](https://www.cookieyes.com/blog/cookie-consent-exemption-for-strictly-necessary-cookies/)

**Eksempler på strictly necessary cookies:**
- Session/authentication cookies
- Shopping cart cookies
- Security cookies (CSRF tokens)
- User preference cookies (language, accessibility)

**Family Budget bruger kun:**
- Session cookie til login (strictly necessary)
- Ingen analytics, tracking eller marketing

### Hvad kræver consent?

Disse cookies kræver eksplicit samtykke:
- Analytics (Google Analytics, Plausible, etc.)
- Marketing/advertising cookies
- Social media tracking
- Third-party cookies generelt

---

## Minimumskrav for Family Budget

### 1. Privacy Policy Side (PÅKRÆVET)

Selvom consent pop-up ikke er nødvendig, skal du informere brugere om:

**Skal indeholde:**
- [ ] Hvem er dataansvarlig (dit navn/virksomhed)
- [ ] Hvilke data indsamles (brugernavn, email hvis opgivet, budget data)
- [ ] Formål med dataindsamling (login, password reset)
- [ ] Hvor længe data gemmes
- [ ] Brugerens rettigheder (indsigt, sletning, etc.)
- [ ] Kontaktinfo til henvendelser

**Eksempel på simpel tekst:**
```
Vi gemmer kun de data du selv indtaster:
- Brugernavn og kodeord (krypteret)
- Email (kun hvis du selv tilføjer den)
- Dine budget-data (indkomst og udgifter)

Dine data bruges kun til at vise dit budget og sende password-reset mails.
Vi deler aldrig dine data med tredjeparter.
```

### 2. Cookie Info (ANBEFALET men ikke pop-up)

Nævn i Privacy Policy:
```
Vi bruger en session-cookie til at holde dig logget ind.
Denne cookie slettes når du logger ud eller lukker browseren.
Vi bruger ingen tracking eller analytics cookies.
```

### 3. Ingen Consent Banner Nødvendig

Fordi alle cookies er strictly necessary, er pop-up consent **ikke påkrævet**.

---

## Implementeringsforslag

### Option A: Minimal (opfylder krav)
- Tilføj `/budget/privacy` side med tekst
- Link i footer: "Privatlivspolitik"

### Option B: Lidt mere professionel
- Privacy Policy side
- Lille ikke-blokerende banner ved første besøg:
  > "Vi bruger kun nødvendige cookies til login. [Læs mere](/privacy)"
- Ingen accept-knap nødvendig (da det er strictly necessary)

### Option C: Overkill (men trygt)
- Full cookie consent banner med accept/decline
- Gemmer samtykke i localStorage
- Unødvendig juridisk, men kan give brugere tryghed

**Anbefaling:** Option A eller B er tilstrækkeligt.

---

## 2025 GDPR Fokusområder

Selvom det ikke påvirker Family Budget direkte:

1. **Dark patterns** - Regulatorer slår ned på manipulerende design
   - "Accept all" vs "Reject all" knapper skal være lige synlige
   - Ingen pre-checkede bokse

2. **Prior consent** - Cookies må ikke sættes før samtykke
   - Ikke relevant for strictly necessary cookies

3. **Bøder** - Op til 4% af global omsætning
   - Primært rettet mod store virksomheder med tracking

---

## Kilder

- [GDPR.eu - Cookies](https://gdpr.eu/cookies/)
- [CookieYes - Cookie Consent Exemption](https://www.cookieyes.com/blog/cookie-consent-exemption-for-strictly-necessary-cookies/)
- [iubenda - Cookies and GDPR](https://www.iubenda.com/en/help/5525-cookies-gdpr-requirements)
- [Plausible - Cookie Consent Banners](https://plausible.io/blog/cookie-consent-banners)
- [Secure Privacy - GDPR 2025](https://secureprivacy.ai/blog/gdpr-cookie-consent-requirements-2025)
- [Usercentrics - EU Cookie Compliance](https://usercentrics.com/knowledge-hub/eu-cookie-compliance/)

---

## Konklusion

Family Budget kan køre lovligt med en simpel Privacy Policy side uden cookie consent pop-up, fordi:

1. Session cookies til auth er strictly necessary (undtaget fra consent)
2. Ingen third-party cookies eller tracking
3. Data gemmes lokalt i SQLite (ingen cloud/third-party)

**Næste skridt:**
- [ ] Opret `/budget/privacy` endpoint
- [ ] Skriv Privacy Policy tekst
- [ ] Tilføj link i footer
