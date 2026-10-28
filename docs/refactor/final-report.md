# DermaScan AI — Safe refactor review report (29/10/2026)

## Source, scope, constraints

- Original: `LePhanHieu/Test2`, `feature/real-data-bootstrap`, SHA
  `aa48e60797b6aa19004e9b1ddb4fb26b9cbdcbd8`.
- Isolated local branch: `chore/test-isolation-audit`. Nothing pushed or merged.
- No schema/migration edits, file deletion, business-flow changes or AI weight changes.
- Synthetic test data, temporary SQLite/storage, mocked email and network.

## Evidence: baseline versus reviewed branch

| Quality signal | Original baseline | Review checkpoint | Interpretation |
| --- | --- | --- | --- |
| Pytest safe suite | 69 passed | **124 passed**, 39.46s | +55 safe tests; excludes live legacy E2E |
| Backend statement coverage | 46% of 4,114 statements | **63% of 4,117 statements**, 1,512 missed | Covers Python `skin_cancer.webapp`, not AI inference or visual UI |
| Ruff full check findings | 114 (original audit) | **8** (7 F401, 1 F841) | Still nonzero; checks/options must be compared carefully |
| Bandit | 16 (12 Low, 4 Medium, 0 High) | **16 (12 Low, 4 Medium, 0 High)** | Findings require triage; no automatic vulnerability or false-positive assumption |
| UI structural smoke | Not measured | 6 structural + 4 token + 3 keyboard + 3 JS-template assertions | DOM/source checks only; **no browser screenshots** |

`pytest` and coverage completed in the isolated worktree with `-p
no:cacheprovider` and a dedicated `--basetemp`. Runtime-dependent tests do
not exercise real AI checkpoint inference, full Celery dispatch or live SMTP.
The browser matrix (320/375/390/768/1024/1440px, 200% zoom) remains open.

## Local commits by work package

| Work | Commit | Result |
| --- | --- | --- |
| Task 0 | `c87f0a3` | Runtime isolation fixtures and baseline |
| Task 1 | `8384965` | CI and quality gates |
| Task 2 | `c7e9238` | Statistics/cache error fix and regression tests |
| Task 3 | `ba78160` | Authentication/roles characterization |
| Task 4 | `dd16dd3` | Batch and async polling contracts |
| Task 5 | `84354b0` | Case ownership and review contracts |
| Task 6 | `85c7a93` | Report, measurement and email contracts |
| Task 7 | `6088819` | Pure email text extraction plus refactor log |
| Task 8 | `6857ba8` | UI inventory and DOM smoke |
| Task 9 | `626ed52` | Shared green-orange tokens and scoped focus states |
| Task 10 | `386f529` | Modal focus/ARIA and tab state synchronization |
| Task 11 | `40a8d30` | JS/template dependency contracts and extraction gate |

## Unresolved and nonblocking review requirements

1. **Browser regression:** no Playwright/Chromium available in the execution
   environment; no screenshots or interactive viewport verification. Keyboard
   changes pass static tests but must be verified live before release.
2. **AI/background processing:** Task 4 polls `PENDING`/`FAILED`, not actual
   Celery/thread dispatch, Grad-CAM or real checkpoints.
3. **Legacy lint/security:** 8 Ruff findings and 16 Bandit findings remain;
   report service and upload/measurement internals have significant risk if
   refactored without stronger tests.
4. **Data governance:** 133 tracked `instance/` paths can contain databases,
   generated medical images and CSVs. The audit did not inspect data contents.
   Inventory/retention/privacy approval is separate from code review.
5. **File deletion gate:** no candidate approved. One manual E2E script is an
   uncertain archival candidate; all schema, database, images, notebooks,
   model weights and dynamic routes remain protected.
6. **Figma:** no design file URL to compare against; no Figma changes made.

## Release gate and safe handoff

- Review the isolated commits and run the safe CI test matrix in a disposable
  environment, including coverage, Ruff and Bandit checks.
- Establish a fully isolated browser harness, capture synthetic screenshots
  and validate modal/tab keyboard behavior and responsive layout before UI
  release. Do not test against real patient records.
- Do not run `test_all_features_e2e.py` until its DB, AI, cache, network and
  output paths are verified isolated.
- Roll back any specific code change by reverting its **individual commit**
  on this branch after review; do not reset the user's original feature branch.
- **Do not merge or push without explicit direction.** For deletion, require
  exact-path approval with a backup/retention decision first.

This report is a review checkpoint, **not a production release certification**.
