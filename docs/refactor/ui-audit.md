# DermaScan AI — UI inventory and baseline (Task 8)

**Scope:** Source-based audit of ADMIN, DOCTOR and USER views at the isolated
worktree. No CSS, layout, JS, workflow or Figma design has been modified.
Browser/visual results are **not** claimed: Playwright is not installed in the
current test environment and no Figma file link was supplied.

## Component and selector inventory

| Role | Existing controls and hooks | Style ownership | JS consumer |
| --- | --- | --- | --- |
| ADMIN | Sidebar `#sidebar`, account filters, case filters `#case-search`, `#case-status`, `#case-doctor`, `#case-from`, `#case-to`; `#profile-2fa`, `#doctor-rejection-dialog`, `#admin-case-modal` | `admin.css`, `admin-doctor-theme.css`, `homepage-management.css` | `admin.js`, `admin_cases.js`, `homepage_management.js` |
| DOCTOR | `[data-tab]` nav in `#doctorNav`; `#patientSelect`, `#imageInput`, `#analyzeBtn`, note/conclusion/recommendation, statistics actions | `style.css`, `workflow.css`, `doctor-analysis-layout.css`, inline `index.html` | `main.js`, `focus_region.js`, `timeline.js` |
| USER | `[data-ptab]` nav in `#patientNav`; registration `#hpRegAgree`, `#hpAuthModal`, `#patientCaseDetailModal`, `#temporaryPatientModal` | `style.css`, `patient.css`, inline `index.html` | `main.js`, `patient.js` |

## Findings and change candidates

| Priority | Evidence | Assessment / next verification |
| --- | --- | --- |
| P1 | `.patient-modal`, `.patient-modal-dialog`, `.patient-modal-backdrop` are declared in `workflow.css` and later `patient.css`; latter changes z-index/layout/width/padding/blur | Cascade collision; take screenshots of dialog variants at 320/390/768/1440 before scoped CSS edits |
| P1 | `admin.html` homepage-management tablist uses `[data-hm-tab]` buttons without per-tab `role=tab` and `aria-selected`; `homepage_management.js` changes active class | Test keyboard/ARIA sync; preserve existing tab switches |
| P1 | `index.html` auth tab uses `role=tab` but does not synchronize `aria-selected` with `.is-active` | Test login/register switching including keyboard |
| P1 | `index.html` auth modal sets initial focus, but focus trap and return-to-opener are not verified | Browser test Tab/Shift+Tab/Escape; do not change behavior without baseline |
| P2 | Button families `.primary`, `.btn-primary`, `.workflow-action-btn`, `.workflow-small-btn`, `.hp-auth-btn` span role-specific styles | Introduce scoped tokens/components in Task 9; preserve IDs/data attributes/class hooks used by JS |
| P2 | CSS breakpoints range across 520, 560, 600, 650, 720, 768, 800, 850, 900, 960, 1050, 1100px | Browser checks at 320/375/390/768/1024/1440 and 200% zoom |
| P2 | `index.html` contains multiple inline style blocks plus external Tailwind CDN | Audit precedence; do not reorder/remove without screenshots |

## Baseline test matrix and limitations

| Role | 320px | 375/390px | 768px | 1024px | 1440px |
| --- | --- | --- | --- | --- | --- |
| ADMIN | Not run | Not run | Not run | Not run | Not run |
| DOCTOR | Not run | Not run | Not run | Not run | Not run |
| USER | Not run | Not run | Not run | Not run | Not run |

`tests/test_ui_structure_smoke.py` checks retained DOM hooks, control families,
checkbox identifiers and existing responsive styles in static templates. These
tests are **not** Playwright or visual regression. The Python `database_app`
is API-only; running a browser requires a separate isolated application harness
without loading real AI weights or contacting external services.

## Task 9 entry criteria

1. Build safe browser harness and install browser dependencies only with allowed permissions.
2. Capture synthetic screenshots at each viewport for dialogs, checked,
   disabled, focused, error, loading and empty controls.
3. Validate no horizontal overflow and focus restoration, then introduce green
   `#2ba149` / orange `#fd8624` tokens with strictly scoped CSS changes.
4. Keep `#id`, `[data-*]`, `.hidden`, `.active`, `.is-active`, `.open`, script
   order and API contracts stable.

No deletion or merge is authorized by this audit.
