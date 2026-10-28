# JS/template extraction gate — Task 11

## Current shared state and module ownership

| Module | Responsibilities | Dependency evidence | Decision |
| --- | --- | --- | --- |
| `static/js/admin.js` | Dashboard, account controls, CSRF/API, HTML escape (`&#039;`) | Loaded first in `admin.html`; shared admin DOM | Preserve current script load position |
| `static/js/admin_cases.js` | Read-only case table/details, filter values, HTML escape (`&#39;`) | Loaded after `admin.js`; uses `#case-*` hooks | Retain module boundary; do not move escaping across IIFEs yet |
| `static/js/homepage_management.js` | Preview, edit, calendar, pending file state and save, HTML escape (`&#39;`) | `#module-homepage`, `[data-hm-tab]`; loaded last in admin | Retain save/preview transaction and state ordering |
| `static/js/main.js` | Doctor analysis/upload, history/stats and home controls | Loaded after focus-region and timeline helpers | Defer splitting until browser/network characterization |
| `static/js/patient.js` | Patient timeline, profile and report view | Loaded after `main.js` | Preserve dynamic panel IDs and event order |

## Why no extraction this batch

- The three HTML escaping helpers look duplicated, but they encode apostrophes
  with different equivalent entities; replacing them changes the serialized
  HTML. The module closures and dynamic consumers need browser assertions.
- Breaking up `main.js` before inspecting event listeners/API requests could
  inadvertently rebind upload, analyze or review handlers.
- Existing role templates include inline JS and several script dependencies.
  `tests/test_js_template_contract.py` now locks loading order and important
  `#id`/`[data-*]` hooks, but is *not* a browser characterization.

## Safe next extraction gate

1. Use an isolated browser with synthetic accounts, mock network/service calls.
2. Record DOM event flow and outgoing request URL/body for one repeated
   component; compare old/new exactly.
3. Move one helper with explicit inputs, retain escape output, then run
   browser checks plus the full Python regression suite.

No JS/template file is deleted or merged in Task 11. No change to API,
database schema or model behavior.
