# Jaxon legal pages and launch review

Prepared November 19, 2026. This is a working inventory and review checklist,
not a determination that Jaxon complies with every applicable law. Have a lawyer
familiar with software and financial-data privacy review the final documents.

## Pages now available

| Link | Route | Purpose | Status |
| --- | --- | --- | --- |
| Privacy policy | `/privacy` | Explain collection, purposes, providers, storage, retention, and user choices | Draft; not effective |
| Terms of use | `/terms` | Define account responsibilities, permitted use, service limitations, and contract terms | Draft; not effective |
| Cookies & storage | `/cookies` | Describe sign-in cookies, theme storage, and browser controls | Draft; not effective |

These links appear in the marketing footer and authentication layout. Draft
pages use `noindex` and a visible draft notice. They do not announce an effective
date, invent an operator/contact, or claim comprehensive legal compliance.
No terms-acceptance system, privacy-request workflow, or cookie-consent manager
has been added by creating the pages.

Public page routes live in `everwealth/web/marketing.py`; authenticated dashboard
routes remain in `everwealth/web/dashboard.py`.

## What is required versus useful

- **Privacy notice:** often a legal requirement, with scope depending on users,
  location, information collected, and business activities. For example,
  [California DOJ's CalOPPA guidance](https://www.oag.ca.gov/privacy/facts/online-privacy/privacy-policy)
  explains the notice requirement for commercial websites collecting personal
  information from California consumers. A small business should not assume that
  being below a different privacy law's size thresholds removes every notice duty.
- **Terms:** a useful contract for a SaaS product; not a universal requirement
  simply because a website exists. Review eligibility, charges, cancellation,
  intellectual property, service changes, liability, dispute procedures, and
  consumer rights for the actual business. Footer links alone should not be
  treated as proof that a user agreed to a contract.
- **Storage notice and consent:** disclose actual cookies and local storage.
  Whether consent is needed depends on purpose, duration, and jurisdiction.
  [ICO guidance](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guide-to-pecr/cookies-and-similar-technologies/)
  distinguishes essential-use exemptions from storage needing consent and notes
  that local storage is also covered. Check the current detailed guidance for
  the launch jurisdiction; the ICO flags that its guidance is being revised.
  Do not assume a persistent login cookie or a theme preference is exempt just
  because it is useful. A footer notice does not itself obtain consent.
- **Contact and privacy requests:** provide a real, monitored contact and a
  working process for requests. Publish deadlines or rights statements only
  after their applicability and the operational process are established.
- **Conditional additions:** paid plans need accurate billing, renewal,
  cancellation and refund disclosures. Regional privacy rights, opt-out links,
  international processing disclosures, and children's rules require an
  applicability review. Do not add decorative “Do Not Sell” or compliance badges
  without the corresponding practices and mechanisms.

## Facts verified in the repository

| Area | Current implementation | Evidence |
| --- | --- | --- |
| Account data | Username, email, password hash; optional profile names | `auth/models/users.py`, `auth/web.py`, `web/settings.py` |
| Financial records | Account identifiers/names/types, budgets, categories, transaction dates/descriptions/amounts/notes, retained original transaction values | `accounts/models.py`, `budgets/models/budgets.py`, `transactions/models.py` |
| Bank linking | Plaid account linking and transaction sync; provider access tokens are stored | `accounts/web.py`, `accounts/models.py`, `transactions/plaid_sync.py` |
| Email | Optional SMTP messages for OTP sign-in | `auth/models/otp.py`, `config.py` |
| Logs | IP address, method, request path/query, response status/timing, diagnostic errors | `main.py` |
| Sign-in storage | First-party `session` cookie, HttpOnly, SameSite=Lax; Secure is configuration-dependent | `auth/web.py` |
| Session lifetime | Normally ten days; logout clears the browser cookie | `auth/models/sessions.py`, `auth/web.py` |
| Theme storage | Browser local storage key `theme`, without an automatic expiry | `templates/header.html`, `static/src/app.js` |

Source paths in the evidence column are relative to `everwealth/`. This inventory
does not verify the live hosting configuration, provider-side tracking, backup
settings, or business activity outside the codebase. In particular, do not claim
“encrypted at rest,” “never shares data,” or a deletion timeframe from this
inventory alone.

## Details the owner must supply

- Legal operator/business name, country/state, public business contact, and a
  monitored privacy/support email. Include a public address if applicable law
  requires it; do not automatically publish a personal home address.
- Launch countries, intended audience and minimum age, and whether paid plans
  or subscriptions will be offered.
- Actual hosting/database/email providers and processing locations; contracts
  and any applicable data-processing or international-transfer arrangements.
- Data-sharing, advertising, analytics, sale/sharing, and browser-signal practices,
  including any deployment features not visible in this repository.
- Retention/deletion rules for accounts, transactions, financial connection
  tokens, logs, uploads, and backups.
- How users can request access, correction, export, account closure, deletion,
  or appeal where applicable, and how identity and responses will be handled.
- How policy changes are communicated, final version/effective dates, and an
  archive of prior effective versions.

## Operational work before treating the drafts as final

1. Confirm the owner details and launch scope above and have the drafts reviewed.
   Publish only promises the business can honor. The
   [FTC's privacy/security guidance](https://www.ftc.gov/business-guidance/privacy-security)
   emphasizes that businesses must follow their privacy representations.
2. Review financial-data obligations, not just website copy. Depending on actual
   activities, a financial-data service may need a review of GLBA and the
   [FTC Safeguards Rule](https://www.ftc.gov/business-guidance/resources/ftc-safeguards-rule-what-your-business-needs-know).
   This checklist does not classify Jaxon as covered or exempt.
3. Verify provider agreements and notices, including
   [Plaid's terms](https://plaid.com/legal/terms-of-use/) and
   [privacy disclosures](https://plaid.com/legal/). Plaid's notices do not replace
   Jaxon's own disclosures or any required user permissions.
4. Implement and exercise the promised account/data-request process. Hiding a
   transaction and logging out are not account deletion or data export.
5. Review the live HTTPS/cookie configuration, access controls, provider-token
   protection, logs, backups, and incident-response process. A policy cannot
   substitute for these controls.
6. If needed, add purpose-specific cookie choices before applicable storage
   occurs, with a way to withdraw consent. Do not treat a link, banner dismissal,
   or acceptance of terms as blanket permission for tracking.
7. Decide how to obtain and record agreement to final terms, including policy
   version and time. Privacy notices inform users; they should not be described
   as a blanket consent to all processing.
8. Replace unresolved draft text, set actual effective dates, update the shared
   draft layout, and remove `noindex` only when the documents are ready for use.
   Keep a record of the adopted versions.
