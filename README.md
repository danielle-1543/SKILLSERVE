# SkillServe file guide

Every major screen or action has a named view file. Start with this table when
you want to change a feature. Paths are relative to this project folder.

| Feature | Python view file | HTML template |
| --- | --- | --- |
| Admin dashboard | `accounts/views/admin/dashboard.py` | `templates/admin_pages/admin_dashboard.html` |
| Admin announcement management | `accounts/views/admin/announcements.py` | `templates/admin_pages/CRUD_annoucements.html` |
| Admin login | `accounts/views/admin/login.py` | `templates/accounts/admin_login.html` |
| Worker verification and feedback | `accounts/views/admin/worker_verification.py` | `templates/admin_pages/worker_reviews.html`, `review_worker.html` |
| Worker dashboard / profile status | `accounts/views/worker/dashboard.py` | `templates/workers/profile.html` |
| Work updates (create, like, delete) | `accounts/views/worker/posts.py` | `templates/workers/tabs/posts.html` |
| Edit and submit worker profile | `accounts/views/worker/profile.py` | `templates/workers/edit_profile.html` |
| View private worker proof | `accounts/views/worker/proof_preview.py` | Inline preview response |
| Worker-only access checks | `accounts/views/worker/access.py` | Shared access guard |
| Client dashboard | `accounts/views/client/dashboard.py` | `templates/clients/dashboard.html` |
| Member login and role routing | `accounts/views/auth/login.py` | Login modal in `templates/public/skillserve.html` |
| Signup | `accounts/views/auth/signup.py` | `templates/accounts/signup.html` |
| PESO homepage | `accounts/views/public/peso_home.py` | `templates/public/dashboard.html` |
| SkillServe landing | `accounts/views/public/skillserve_home.py` | `templates/public/skillserve.html` |
| Shared public announcement | `accounts/views/public/announcement.py` | `templates/public/announcement.html` |

The worker dashboard currently shows the worker profile, verification status,
and review history. Its existing `/worker/profile/` URL is preserved.
The `/dashboard/` entry renders the client dashboard and forwards workers and
administrators to their corresponding screens.

## Shared code

- `accounts/urls.py`: application URLs, grouped by public/authentication/account role.
- `config/urls.py`: includes application routes, Django admin, and public media.
- `accounts/forms/auth.py`: signup and administrator login validation.
- `accounts/forms/worker.py`: worker profile, services, training, and upload validation.
- `accounts/forms/admin.py`: verification decisions and required feedback.
- `core/forms.py`: announcement validation and image checks.
- `accounts/models.py`: shared user and worker-profile database models.
- `core/models.py`: announcement database model.
- `accounts/migrations/`, `core/migrations/`: database schema history; keep these files.
- `accounts/tests/`, `core/tests.py`: automated tests.

Models stay in their existing Django apps to keep database relationships and
migrations simple. Organizing Python files does not duplicate accounts or create
separate databases for each role.

## Templates and styles

Templates are grouped in `templates/admin_pages/`, `templates/workers/`,
`templates/clients/`, `templates/accounts/` (shared authentication), and
`templates/public/`. Shared profile details and feedback are included as partials
rather than duplicated across worker and administrator screens.

- `static/css/base.css`: shared layout, components, and announcement management.
- `static/css/public.css`: public pages, navigation, login/signup, and sharing.
- `static/css/workers.css`: worker profiles and administrator verification screens.
- `static/images/`: logo assets.

## Database and files

`db.sqlite3` stores application data. `media/` stores public announcement photos.
`private_uploads/` stores worker proof served only through authenticated inline previews.
Keep credentials in the database, not in source files.

## Local development

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Checks:

```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

## Worker profile tabs

The profile dashboard now uses `templates/workers/profile.html` for the cover,
identity header, tabs, and sidebar. Individual tab content is in:

- `templates/workers/tabs/resume.html`
- `templates/workers/tabs/posts.html`
- `templates/workers/tabs/reviews.html`

`static/css/worker_dashboard.css` styles this screen separately from the worker
profile editor. `accounts/forms/worker_posts.py` validates the work-update composer.
Posts are stored in `WorkerPost`; client feedback is stored in `WorkerClientReview`.
Client review submission is reserved for the future completed-service workflow;
the current Reviews tab displays saved reviews without inventing sample ratings.
Administrator verification feedback remains separate in `WorkerReview`.

Worker posts support an optional JPG, PNG, or WebP photo (up to 5 MB), either by
itself or alongside text. The preview logic is in `static/js/worker_posts.js`,
validation is in `accounts/forms/worker_posts.py`, and the post template is
`templates/workers/tabs/posts.html`. Post images use public media storage;
verification proof remains separate and private.

## Client dashboard search

`accounts/views/client/dashboard.py` handles verified-worker keyword, location,
and service-category searches. The page layout and category/announcement cards
are in `templates/clients/dashboard.html`; styling is in
`static/css/client_dashboard.css`. Only active, verified worker accounts appear
in search results. Recent announcements are read from the announcement database.

## Client discovery and interactions

- `accounts/views/client/search.py`: dedicated paginated search results.
- `accounts/views/client/worker_profile.py`: client-visible verified resume, posts, reviews.
- `accounts/views/client/bookmarks.py`: save/remove bookmarks and the Saved workers page.
- `accounts/views/client/reports.py`: report submission.
- `accounts/views/client/access.py`: client role checks and verified-profile visibility.
- `accounts/views/messaging.py`: inbox, conversation creation, participant-only messages.
- `accounts/views/admin/reports.py`: report review queue.
- `accounts/forms/client.py`: message and report validation.
- `templates/clients/search.html`, `worker_cards.html`, `worker_profile.html`: discovery UI.
- `templates/messages/`: inbox and conversation UI; styled by `static/css/messaging.css`.

Search results contain only verified, active worker accounts. Private worker proof
and administrator verification feedback are excluded from client profile views.
Chat messages are persisted and visible only to the client and worker in a thread.
The current messaging screen updates when refreshed; it does not use live push.

## Messenger-style chat

`accounts/views/messaging.py` handles private conversations, automatic updates,
reply references, seen timestamps, emoji reactions, and unsending your own messages.
The UI is split into `templates/messages/sidebar.html`, `avatar.html`,
`message_list.html`, and `conversation.html`. Styling is in
`static/css/messaging.css`; chat interactions and four-second polling are in
`static/js/messaging.js`. Avatars use account initials with a worker badge.
Online/typing indicators and audio/video calling are not implemented.

## Chat attachments and booking tickets

- `accounts/forms/chat_uploads.py`: multiple attachment and file-type validation.
- `accounts/views/chat_attachments.py`: participant-only file access and video byte ranges.
- `accounts/forms/booking.py`: structured service, location, rate, contact, and schedule fields.
- `accounts/views/bookings.py`: booking creation and role-specific status transitions.
- `templates/messages/booking_modal.html`: Book worker form.
- `templates/messages/booking_tickets.html`: shared ticket details, statuses, actions, and history.

Chat accepts up to five attachments, 25 MB per file and 50 MB total: JPG, PNG,
WebP, MP4, WebM, PDF, UTF-8 TXT, DOCX, XLSX, and PPTX. Files use private storage;
images and videos display in chat, while documents open or download according to
their format. Unsent-message attachments are no longer accessible.

Booking flow: Requested -> Accepted -> In progress -> Awaiting client confirmation
-> Completed. Workers accept/decline requests, start work, and mark work finished.
Clients can cancel before work begins and confirm the completed service. Status
changes are recorded with actor and time, and stale actions are rejected.
Booking forms save structured fields for future export and AI assistance; neither
AI conversation analysis nor automatic export is active yet.

## Client profiles and privacy

`accounts/views/client/profile.py` renders each client's public authored reviews
and private saved workers. `templates/clients/profile.html` and
`static/css/client_profile.css` implement the profile UI. `/client/profile/` is
the signed-in client's own profile; `/clients/<id>/` exposes only public reviews
and account display identity. Favorites are queried only for the owner, and other
visitors receive 404 if they request the saved tab. Emails/contact information
and private favorites are not included in public profile markup.


Client job offers: `accounts/views/job_offers.py`, `accounts/forms/job_offers.py`, `templates/jobs/`, and `static/css/job_offers.css`. `/jobs/` shows clients their own posts and workers recent open future offers with search and pagination. Clients publish at `/jobs/new/` and close their posts. Workers can comment or start the existing private client-worker conversation. Posts collect general area, job type, description, schedule, optional preferences and PHP budget; exact addresses/contact details should be shared privately. JobOffer and JobComment records are in the database (migration 0010). Job posts do not automatically create a booking; bookings remain in chat.


Shared design system: `static/css/redesign.css` contains the navy/gold/green/burgundy palette. `templates/accounts/base.html` and `templates/accounts/navigation.html` provide signed-in side navigation for clients and workers; the admin shell includes the same navigation. `static/js/navigation.js` handles the = toggle, desktop preference storage, mobile overlay, Escape, and hidden navigation focus handling. Public pages retain top navigation.


Database consolidation: migration 0012 replaces the separate chat/job attachment tables with accounts_attachment. ChatAttachment and JobAttachment are proxy models with separate ownership filters. Both retain the existing endpoints and private storage. See DATABASE_AUDIT.md for backup and migration verification.


Skills catalog: administrators manage categories and suggested tags at /admin-dashboard/skills/ (accounts/views/admin/skills_catalog.py). Worker specialty selection uses accounts/forms/skills.py, templates/workers/skills_editor.html and static/js/worker_skills.js. Categories are fixed by admins; specialties may be suggested tags or worker-specific custom text. Admins can explicitly promote custom text to a shared suggestion. Used catalog entries are protected from deletion and can instead be deactivated. Existing inactive selections are retained but cannot be newly added. The catalog starts empty; create approved categories before workers submit. Existing legacy skills/services are retained and searchable. Schema migration: 0013_skills_catalog.


Unified login: all SkillServe accounts use /login/ and the member modal. The former /admin-login/ and native /admin/login/ entry points redirect to it. Application admin access uses the admin role (with compatibility for legacy staff accounts with an unspecified role). Authenticated non-admin users receive 403 on application administration routes. Category slugs are generated automatically at creation and remain stable after renaming; admins do not enter them.


Catalog simplification (migration 0014): availability flags and activate/deactivate actions were removed. Add/edit a category and its suggested specialties together using one specialty per line. Used entries cannot be deleted; names can be edited. Category deletion removes its unused suggested tags atomically and is blocked if any worker selections would be affected. Worker custom specialties stay profile-specific; the promotion/review queue was removed. Existing catalog/profile records were preserved, with a backup before migration.
