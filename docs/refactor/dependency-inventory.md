# Repository dependency inventory — Task 12

Source: `LePhanHieu/Test2`, original `feature/real-data-bootstrap`
`aa48e60797b6aa19004e9b1ddb4fb26b9cbdcbd8`, audited on isolated
`chore/test-isolation-audit`. Read-only inventory: no file contents from
database, medical imagery or checkpoints were inspected.

## Tracked assets at inventory time

- 336 tracked files in the Task 12 worktree before adding this inventory.
- 83 tracked paths within `skin_cancer/webapp/` (application, static and templates).
- 133 tracked paths under `instance/`, including SQLite files, images, CSVs,
  Grad-CAM and measurements. **Potential personal/sensitive data:** protect.
- 5 tracked Alembic revisions under `migrations/versions/`; preserve all.
- Four model weight files under `skin_cancer/checkpoints/` and
  `skin_cancer/class_weights_*.pt`; preserve all.
- Five research `.ipynb` files in `skin_cancer/notebooks/`; preserve.

## Dynamic consumers and contract anchors

| Target | Consumers / proof | Classification |
| --- | --- | --- |
| `skin_cancer/webapp/database_app.py` | Flask CLI, `create_app`, tests, and `app.py` bootstrap | Protected |
| `skin_cancer/webapp/app.py` | `python -m skin_cancer.webapp.app`, AI loading and analyze endpoint | Protected |
| `skin_cancer/webapp/seed.py` | Registered `seed-demo` CLI; not automatically enabled by tests | Uncertain legacy operation; **do not delete** |
| `skin_cancer/webapp/routes/*.py`, `services/*.py`, `models/*.py` | Flask blueprint registration, dynamic imports, tests; see `bootstrap.py` | Protected pending per-module call graph |
| `skin_cancer/webapp/templates/{index,admin}.html` | Root/admin views and inline DOM/JS hooks | Protected |
| `skin_cancer/webapp/static/js/*.js` | Templates script src; dynamic selectors listed in `js-template-audit.md` | Protected |
| `skin_cancer/webapp/static/css/*.css` | Templates stylesheets; role cascade listed in `ui-audit.md` | Protected |
| `test_all_features_e2e.py` | Standalone legacy manual E2E; excluded by pytest.ini/CI, referenced in README | Manual-only; candidate for future archival, not deletion yet |
| `instance/**` | Runtime DB/cache, generated reports, images and exports; contents may be referenced by DB paths | Sensitive data; protected, do not move/delete |
| `migrations/**` | Alembic history and integrity of deployed database | Protected; no schema edits |
| `skin_cancer/checkpoints/**`, `skin_cancer/notebooks/**` | AI inference/reproducibility and research evidence | Protected |

## Verification limits

- `rg` and static search cannot resolve dynamic imports, Jinja includes,
  runtime filenames, CLI entrypoints, JS selectors, serialized database paths
  or research references with certainty.
- Tests do not run legacy E2E, actual AI weights, browser automation or live SMTP.
- Tracked `instance/` content is a governance/privacy concern, **not** evidence
  that any file is safe to delete; no contents were opened or altered.

An exact-path deletion proposal requires owner approval and independent
backup/retention review before any action; see `deletion-proposals.md`.
