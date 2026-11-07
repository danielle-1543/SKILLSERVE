# Attachment consolidation completed

Applied migration `accounts.0012_consolidate_attachments` on 6 November 2026 after a full backup and 64 passing tests.

- Table count: **31 → 30**.
- `accounts_chatattachment` and `accounts_jobattachment` were replaced by **`accounts_attachment`**.
- Feature-specific ChatAttachment and JobAttachment are now proxy models: they query the same physical table, with separate ownership filters. They do not create tables.
- Every attachment must belong to exactly one chat message or job offer (database check constraint).
- Existing private storage paths and download permissions are retained. Neither file blobs nor folders were moved.
- Both old attachment tables had zero records in the live database. Migration tests also exercised populated tables and reversal, preserving IDs, owner links, paths and chat size metadata.
- All other SkillServe table contents were compared before/after and remained unchanged.
- SQLite integrity and foreign-key checks passed. No model/migration drift was detected.
- Migration stops atomically if IDs overlap between populated legacy attachment tables rather than silently changing file URLs. No overlap existed here.

Backup immediately before applying the migration: `backups/skillserve-attachment-merge-final-20261106-155411.sqlite3`.

Rollback migration (preserves new attachment rows by splitting them back by owner):

```powershell
.\.venv\Scripts\python.exe manage.py migrate accounts 0011_jobattachment
```

A rollback must be paired with reverting the model code to the pre-consolidation version before using the application. The saved database backup is a separate recovery option; restoring it loses any later changes. Restart the development server after code/schema updates if it runs without automatic reload.

## Original inspection (historical, before consolidation)

The remaining sections record the initial inspection; the attachment decision was superseded by the consolidation above.

# SkillServe database audit

Checked 6 November 2026 against the actual db.sqlite3 and current models/views/forms.

31 application/framework tables. SQLite internal tables are excluded. Database integrity: ok. Foreign-key errors: 0.

No tables or records were deleted or merged. An empty table is not evidence that its feature is unused by the code.

| Table | Records at audit | Purpose |
| --- | ---: | --- |
| `accounts_booking` | 1 | Job details, agreed proposal, current booking status and revision. |
| `accounts_bookingevent` | 2 | Multiple dated status changes per booking with the responsible actor. |
| `accounts_chatattachment` | 0 | Multiple private files per message, with file sizes and participant access. |
| `accounts_chatmessage` | 8 | Multiple messages per conversation, including reply/read/unsend state. |
| `accounts_chatreaction` | 0 | One reaction per account/message; multiple people can react. |
| `accounts_conversation` | 1 | One conversation per client/worker pair, shared by messages and bookings. |
| `accounts_jobattachment` | 0 | Multiple files per job offer, accessed through job-post permissions. |
| `accounts_jobcomment` | 1 | Multiple worker/client comments per job offer. |
| `accounts_joboffer` | 3 | Client job offers, public job details and open/closed state. |
| `accounts_savedworker` | 1 | Private client-to-worker bookmarks with duplicate prevention. |
| `accounts_user` | 3 | One shared account table for administrators, clients, and workers. |
| `accounts_user_groups` | 0 | Django account-to-group permission link; currently unused but part of AbstractUser/UserAdmin. |
| `accounts_user_user_permissions` | 0 | Django account-specific permission link; part of AbstractUser/UserAdmin. |
| `accounts_userreport` | 0 | Reports of workers and admin review state. |
| `accounts_workerclientreview` | 0 | Client service ratings/feedback shown on profiles; distinct from admin verification. |
| `accounts_workereducation` | 1 | Multiple education/training entries per worker. |
| `accounts_workerevidence` | 1 | Multiple private proof/certification files per worker. |
| `accounts_workerexperience` | 1 | Multiple work experience entries per worker. |
| `accounts_workerpost` | 1 | Worker portfolio/work updates. |
| `accounts_workerpost_likes` | 0 | Links each liking account to a worker post; many-to-many relationship. |
| `accounts_workerprofile` | 1 | Worker-only professional profile and verification status; links to the account. |
| `accounts_workerreview` | 1 | Administrator verification decisions and feedback history, by submission revision. |
| `accounts_workerservice` | 2 | Multiple services and PHP rates for each worker; searchable individually. |
| `auth_group` | 0 | Django permission groups; currently unused by SkillServe role selection. |
| `auth_group_permissions` | 0 | Links Django groups and permissions. |
| `auth_permission` | 104 | Django permissions used by the installed admin/auth system. |
| `core_announcement` | 1 | PESO announcements, separate from client job offers and worker portfolio posts. |
| `django_admin_log` | 0 | Change history for the installed Django admin. |
| `django_content_type` | 26 | Model registry used by Django permissions and admin. |
| `django_migrations` | 30 | Tracks applied database migrations; prevents recreating existing schema changes. |
| `django_session` | 5 | Stored login sessions. |

## Merge decisions

- Accounts are already consolidated: admin/client/worker roles use accounts_user. A separate worker profile holds worker-specific fields.
- Work experience and education could technically share a typed resume-entry table, but their fields/validation differ. The existing formsets support independent lists. No practical gain justifies introducing unused columns or more type-specific logic.
- Messages, comments, announcements, worker posts and job offers have different ownership, visibility and workflows. Keep them separate.
- Chat and job attachments share validation/storage infrastructure in code. One shared table is possible, but would require alternate parent relationships, constraints and access handling to remove only one table. Keep the explicit ownership relationships.
- Bookings and their events must remain separate to retain multiple dated status changes and actors.
- Admin verification decisions and client ratings must remain separate to avoid mixing private review feedback with public service reviews.
- Group/permission tables are currently empty in places. Removing them requires deliberately replacing Django permission/admin support; do not drop them from Navicat while those models/apps remain installed.
- Repeating child records belong in linked tables. Moving them into JSON, comma-separated fields, or repeated parent rows would reduce table count while weakening validation, search, uniqueness and relationships.

SQL JOIN combines related information for a query/display. It does not require physically merging tables.

## Conclusion

No accidental duplicate or orphan application tables were found in this audit. Keep the schema as it is. Use the purpose map above to distinguish feature data from framework and relationship tables.
