# Deletion proposals — approval gate (no deletion performed)

**Current approved deletions: none.** The list below is informational, not a
deletion instruction. This task has not removed, moved or merged any file.

| Exact path | Classification | References / replacement | Risk and precondition | Decision |
| --- | --- | --- | --- | --- |
| `test_all_features_e2e.py` | Uncertain, archival candidate | Manual-only legacy E2E; `README_PHASE1.md` documents it; CI and `pytest.ini` exclude it | High: may retain unique end-to-end checks; first replace with isolated browser/AI E2E and document equivalent coverage. Prefer archive instead of deletion | **Not approved; retain** |

## Protected — not proposed for deletion

- `instance/cache.db`, `instance/dermascan.db` and every path under
  `instance/uploads/`, `instance/gradcam/`, `instance/measurements/`: may contain
  operational or patient-related data. Never infer expendability from age/name.
- All `migrations/versions/*.py`: schema history is immutable in this refactor.
- `skin_cancer/checkpoints/*.pth`, `skin_cancer/class_weights_*.pt`, all
  `skin_cancer/notebooks/*.ipynb`.
- `skin_cancer/webapp/seed.py`: its `seed-demo` command is still exposed and
  potentially used manually; does not authorize deletion.
- The untracked `.coverage` and test-created
  `instance/uploads/doctor-certificates/` are not staged, deleted or approved.

## Future approval record (blank)

For each exact path: owner decision, backup destination, static/dynamic usage
evidence, replacement test, full regression, rollback commit and date must be
recorded before removal. Any approval must be separate from schema or workflow
changes. Current status: **awaiting any explicit file-specific authorization**.
