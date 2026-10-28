# Backend refactor log

## Scope and risk inventory (Task 7)

The worktree stays isolated from `feature/real-data-bootstrap`. No database
schema, migration, route, public JSON contract or model inference is changed.

| Candidate | Observed responsibility | Risk | Decision |
| --- | --- | --- | --- |
| `services/email_service.py:EmailService.send_report` | Validates, persists send log, builds text, attaches PDF and calls SMTP | Medium: logging and transaction order must remain intact | Extract only plain-text construction into a pure helper |
| `services/report_service.py:ReportService.generate` | Creates PDF, reserves version, publishes file, commits Report | High: atomicity/version collision and file cleanup | Defer until version-conflict characterization tests |
| `services/batch_upload.py:BatchUploadService._process_one` | Validates file, reads bytes, hashes, stores and records DB row | High: failure isolation and file cleanup | Retain current flow; covered partly by Task 4 tests |
| `routes/cases.py:post_case` | Validates registered vs temporary patient and assigns doctor | High: authorization and transactions | Retain until more edge-case contract coverage |
| `services/measurement_service.py:MeasurementService.measure` | Image reading, threshold selection, contours and metrics | High: numerical output and model-independent algorithm | Retain; only synthetic geometry contracts added |

## Refactor 7.1 — email body formatting

- **Prior location:** inline `greeting` and `message.body` assignment in
  `EmailService.send_report`.
- **New callable:** `EmailService._report_email_body(patient_name, case_code)`;
  accepts the same already-normalized strings and returns the same text.
- **Callers:** only `EmailService.send_report`, after the existing case lookup.
- **Side effects preserved:** the `EmailLog` `PENDING` commit happens before
  the message and `mail.send`, then the original `SENT`/`FAILED` commits run
  unmodified. PDF attachment, subject and recipients remain in `send_report`.
- **Characterization:** `tests/test_email_body_contract.py` records the exact
  Vietnamese body and PDF attachment using synthetic patient/case data and
  mocked `mail.send`; also covers missing patient name.
- **Dependencies:** no new production imports; no file deletion.

Do not extract transaction/file-cleanup routines without stronger error-path
tests. The code may appear repetitive but operations have ordering constraints.
