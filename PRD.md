# PRD: Freelancer Manager MVP

## 1. PROJECT OVERVIEW

**What it is:** A single-user freelancer management tool to track clients, projects, tasks, daily to-do lists, time spent per task, and billable hours.

**Who it's for:** A solo freelancer managing multiple clients and projects simultaneously.

**Core Philosophy:** Build the foundation rock-solid first. Every layer depends on the layer below it. No layer gets built until the one below it is tested and working. This is a pyramid, not a pancake.

**What this is NOT:** Not a multi-tenant SaaS. Not a team collaboration tool. Not an invoicing system. No payment processing. No AI features. No real-time notifications. Those are post-MVP.

---

## 2. MVP FEATURE SCOPE (Hard Boundary)

### IN SCOPE

- User registration and login (single user)
- Client CRUD (create, read, update, delete)
- Project CRUD linked to clients
- Task CRUD linked to projects
- Daily to-do list (tasks marked for today)
- Task timer (start/stop per task, cumulative time)
- Task status tracking (todo, in-progress, done)
- Project status tracking (active, on-hold, completed)
- Project deadline with visual attention indicators
- Billable hours summary per project
- Session persistence (stay logged in)

### OUT OF SCOPE (Do Not Build These)

- Multi-user / team features
- Invoicing or payment
- File uploads
- Email notifications
- Charts and graphs beyond simple summaries
- Mobile native apps
- API for third parties
- Dark mode (add post-MVP if time permits)

---

## 3. DATA ARCHITECTURE — THE FOUNDATION

This is the base of the pyramid. Define these schemas completely before writing any application code. Every relationship, every field, every constraint. Do not skip this. Do not "figure it out as you go."

### Entity Relationship Summary

```
User 1──→ * Client 1──→ * Project 1──→ * Task
                                                    │
                                              * TimeEntry
```

### Table: users

| Field         | Type         | Constraints           | Notes                         |
| ------------- | ------------ | --------------------- | ----------------------------- |
| id            | UUID         | PK, auto-generated    |                               |
| username      | VARCHAR(50)  | UNIQUE, NOT NULL      | For login                     |
| email         | VARCHAR(255) | UNIQUE, NOT NULL      |                               |
| password_hash | VARCHAR(255) | NOT NULL              | bcrypt, never store plaintext |
| created_at    | TIMESTAMP    | NOT NULL, DEFAULT NOW |                               |
| updated_at    | TIMESTAMP    | NOT NULL, auto-update |                               |

### Table: clients

| Field      | Type                      | Constraints              | Notes                  |
| ---------- | ------------------------- | ------------------------ | ---------------------- |
| id         | UUID                      | PK                       |                        |
| user_id    | UUID                      | FK → users.id, NOT NULL |                        |
| name       | VARCHAR(255)              | NOT NULL                 | Company or person name |
| email      | VARCHAR(255)              | nullable                 |                        |
| phone      | VARCHAR(50)               | nullable                 |                        |
| company    | VARCHAR(255)              | nullable                 |                        |
| notes      | TEXT                      | nullable                 | Freeform notes         |
| status     | ENUM('active','inactive') | DEFAULT 'active'         |                        |
| created_at | TIMESTAMP                 | NOT NULL, DEFAULT NOW    |                        |
| updated_at | TIMESTAMP                 | NOT NULL, auto-update    |                        |

**Index:** user_id (every query filters by user)

### Table: projects

| Field       | Type                                 | Constraints                | Notes             |
| ----------- | ------------------------------------ | -------------------------- | ----------------- |
| id          | UUID                                 | PK                         |                   |
| user_id     | UUID                                 | FK → users.id, NOT NULL   |                   |
| client_id   | UUID                                 | FK → clients.id, NOT NULL | CASCADE delete    |
| name        | VARCHAR(255)                         | NOT NULL                   |                   |
| description | TEXT                                 | nullable                   |                   |
| status      | ENUM('active','on-hold','completed') | DEFAULT 'active'           |                   |
| deadline    | DATE                                 | nullable                   |                   |
| hourly_rate | DECIMAL(10,2)                        | nullable                   | For billable calc |
| is_billable | BOOLEAN                              | DEFAULT true               |                   |
| created_at  | TIMESTAMP                            | NOT NULL, DEFAULT NOW      |                   |
| updated_at  | TIMESTAMP                            | NOT NULL, auto-update      |                   |

**Indexes:** user_id, client_id
**Constraint:** A project's client must belong to the same user (enforce in application logic)

### Table: tasks

| Field           | Type                              | Constraints                 | Notes                 |
| --------------- | --------------------------------- | --------------------------- | --------------------- |
| id              | UUID                              | PK                          |                       |
| user_id         | UUID                              | FK → users.id, NOT NULL    |                       |
| project_id      | UUID                              | FK → projects.id, NOT NULL | CASCADE delete        |
| title           | VARCHAR(255)                      | NOT NULL                    |                       |
| description     | TEXT                              | nullable                    |                       |
| status          | ENUM('todo','in-progress','done') | DEFAULT 'todo'              |                       |
| priority        | ENUM('low','medium','high')       | DEFAULT 'medium'            |                       |
| is_today        | BOOLEAN                           | DEFAULT false               | Marks for daily to-do |
| estimated_hours | DECIMAL(5,2)                      | nullable                    |                       |
| created_at      | TIMESTAMP                         | NOT NULL, DEFAULT NOW       |                       |
| updated_at      | TIMESTAMP                         | NOT NULL, auto-update       |                       |

**Indexes:** user_id, project_id, status, is_today
**Computed (in queries, not stored):** total_time_spent = SUM of time_entries for this task

### Table: time_entries

| Field            | Type         | Constraints              | Notes                                   |
| ---------------- | ------------ | ------------------------ | --------------------------------------- |
| id               | UUID         | PK                       |                                         |
| user_id          | UUID         | FK → users.id, NOT NULL |                                         |
| task_id          | UUID         | FK → tasks.id, NOT NULL | CASCADE delete                          |
| started_at       | TIMESTAMP    | NOT NULL                 |                                         |
| ended_at         | TIMESTAMP    | nullable                 | NULL = timer running                    |
| duration_seconds | INTEGER      | nullable                 | Computed on stop: ended_at - started_at |
| note             | VARCHAR(500) | nullable                 | What was done in this session           |
| created_at       | TIMESTAMP    | NOT NULL, DEFAULT NOW    |                                         |

**Indexes:** user_id, task_id, started_at
**Constraint:** Only one time_entry per task can have ended_at = NULL at any time (one active timer per task)
**Constraint:** A task's project must belong to the same user (application logic)

---

## 4. DEVELOPMENT PHASES — BUILD ORDER

### CRITICAL RULES FOR THE CODING AGENT

1. **Complete each phase fully before starting the next.**
2. **Write tests for each phase before moving on.**
3. **Do not add UI until Phase 4.** The first three phases are backend-only.
4. **When a phase says "verify," run all tests. If anything fails, fix before proceeding.**
5. **Do not refactor across phases unless a test fails.** Keep moving forward.

---

### PHASE 1: Database Foundation + Basic CRUD API

**Goal:** Database exists, schemas are correct, basic CRUD operations work for every entity.

**Deliverables:**

- Database setup script (migration or schema file)
- Seed script with test data (1 user, 2 clients, 3 projects, 5 tasks)
- CRUD API endpoints for each entity (no auth yet):
  - `POST /api/clients`, `GET /api/clients`, `GET /api/clients/:id`, `PUT /api/clients/:id`, `DELETE /api/clients/:id`
  - Same pattern for `/api/projects`, `/api/tasks`, `/api/time_entries`
- All queries filtered by `user_id` (even without auth, use a hardcoded user_id for now)

**Time Entry Specifics:**

- `POST /api/time_entries` — start timer (omit ended_at)
- `PUT /api/time_entries/:id/stop` — stop timer (set ended_at, compute duration_seconds)
- `GET /api/tasks/:id/time-entries` — get all time entries for a task
- `GET /api/tasks/:id/summary` — return task + total_time_spent (computed)

**Test Suite (Phase 1):**

- Test: Create a client, retrieve it, verify all fields
- Test: Create a project linked to a client, retrieve with client info
- Test: Create a task linked to a project, retrieve with project info
- Test: Start a timer, stop it, verify duration_seconds is correct
- Test: Delete a client cascades to projects and tasks
- Test: Cannot create a project with non-existent client_id (404)
- Test: Cannot create a task with non-existent project_id (404)
- Test: All list endpoints return only data for the test user

**Verify:** All 8+ tests pass. Run them. Do not proceed until they do.

---

### PHASE 2: Authentication & Security

**Goal:** Secure registration and login. Every API endpoint requires authentication. Passwords are properly hashed.

**Deliverables:**

- `POST /api/auth/register` — create account (username, email, password)
  - Validate: password min 8 chars, email format, username 3-50 chars
  - Hash password with bcrypt (cost factor 12)
  - Return user id + username (NOT password_hash)
- `POST /api/auth/login` — authenticate
  - Verify bcrypt hash
  - Generate JWT token (expires in 24h)
  - Return token + user info
- `GET /api/auth/me` — return current user info (requires token)
- Middleware: `requireAuth` — extracts JWT from `Authorization: Bearer <token>` header, attaches user_id to request
- Apply `requireAuth` to ALL `/api/clients`, `/api/projects`, `/api/tasks`, `/api/time_entries` endpoints
- Remove hardcoded user_id from Phase 1 — use `req.user_id` from token

**Security Requirements:**

- JWT secret loaded from environment variable, never hardcoded
- Password hash uses bcrypt, never store or log plaintext passwords
- JWT contains only `user_id` and `iat`/`exp`, nothing else
- Failed login returns generic "Invalid credentials" (do not reveal if username or email is wrong)
- Rate limiting on `/api/auth/login` — max 5 attempts per minute per IP

**Test Suite (Phase 2):**

- Test: Register with valid data returns user (no password_hash in response)
- Test: Register with duplicate username returns 409
- Test: Register with short password returns 422
- Test: Login with correct credentials returns JWT
- Test: Login with wrong password returns 401
- Test: Access `/api/clients` without token returns 401
- Test: Access `/api/clients` with valid token returns data
- Test: Access `/api/clients` with expired token returns 401
- Test: User A cannot see User B's clients (isolation test — create two users)
- Test: Password in database is not plaintext (query raw DB, verify)

**Verify:** All 10+ tests pass. Do not proceed until they do.

---

### PHASE 3: Business Logic Layer

**Goal:** Add the logic that makes this useful — status transitions, today's tasks, billable calculations, deadline awareness.

**Deliverables:**

**Task Status Endpoints:**

- `PATCH /api/tasks/:id/status` — change status with validation:
  - `todo` → `in-progress` or `done`
  - `in-progress` → `todo` or `done`
  - `done` → `todo` or `in-progress`
  - If status changes to `in-progress` and no active timer, suggest starting one (in response metadata, not enforced)
  - If status changes to `done` and timer is running, auto-stop the timer

**Project Status Endpoints:**

- `PATCH /api/projects/:id/status` — change project status
  - If project set to `completed`, return warning if any tasks are not `done`
  - Do not force task completion, but warn

**Today's To-Do List:**

- `GET /api/tasks/today` — returns all tasks where `is_today = true`, grouped by status
- `PATCH /api/tasks/:id/today` — toggle `is_today` boolean
- `POST /api/tasks/today/bulk` — accept array of task_ids to set is_today=true

**Billable Summary:**

- `GET /api/projects/:id/summary` — returns:
  - Project info + client name
  - Total tasks, tasks by status (todo/in-progress/done counts)
  - Total time spent (sum of all task time_entries)
  - Billable amount (total_hours × hourly_rate) if is_billable
  - Is deadline approaching? (deadline within 3 days and status != 'completed')
  - Is deadline overdue? (deadline < today and status != 'completed')

**Dashboard Summary:**

- `GET /api/dashboard` — returns:
  - Active clients count
  - Active projects count
  - Today's task count by status
  - Projects with overdue deadlines (array)
  - Projects with deadlines within 3 days (array)
  - Total billable hours this week (Monday to Sunday of current week)

**Test Suite (Phase 3):**

- Test: Task status transition valid paths work
- Test: Task status cannot be set to invalid value (422)
- Test: Marking task as 'done' auto-stops running timer
- Test: Today's to-do returns only is_today=true tasks
- Test: Toggle is_today works both ways
- Test: Project summary calculates total time correctly across multiple tasks
- Test: Project summary calculates billable amount correctly
- Test: Project summary flags overdue deadline
- Test: Project summary flags approaching deadline (within 3 days)
- Test: Dashboard returns correct counts
- Test: Dashboard week calculation is correct (test with known data)
- Test: Completing a project warns about incomplete tasks (does not block)

**Verify:** All 12+ tests pass. Do not proceed until they do.

---

### PHASE 4: Core UI — Functional First

**Goal:** Build working UI pages. They do not need to be beautiful yet. They need to be functional, clear, and correctly wired to the API. Use a simple component library or minimal custom styling. No animations, no fancy layouts. Information hierarchy matters more than visual polish.

**Tech choice:** Use whichever frontend framework you're strongest in (React, Vue, Svelte — pick one and commit). The backend should be Node.js with Express (or your equivalent). The PRD is framework-agnostic for frontend but assumes a JS/TS full-stack.

**Authentication UI:**

- Login page: username/email + password fields, submit button, link to register
- Register page: username + email + password + confirm password, submit button, link to login
- On successful login, store JWT in httpOnly cookie or secure localStorage
- If not authenticated, redirect to login page
- Logout button in header

**Layout Shell:**

- Top nav: App name (left), Logout button (right)
- Sidebar or top tabs: Dashboard, Clients, Projects, Tasks (Today)
- Active page highlighted
- Responsive: sidebar collapses to hamburger on mobile

**Clients Page:**

- List view: table or card list showing name, company, email, status badge, project count
- "Add Client" button → modal or inline form
- Click client name → Client Detail Page
- Delete with confirmation dialog ("This will also delete all projects and tasks under this client. Are you sure?")
- Status filter (active/inactive/all)

**Client Detail Page:**

- Client info header (name, email, phone, company, status, notes)
- Edit button → inline edit or modal
- Below: list of this client's projects
- Each project shows: name, status badge, deadline (red if overdue, yellow if within 3 days), task count, total hours

**Projects Page:**

- List view: project name, client name, status badge, deadline, task progress (e.g., "3/5 tasks done"), total hours
- "Add Project" button → form with client dropdown (populated from clients), name, description, status, deadline, hourly_rate, is_billable toggle
- Filter by client, filter by status
- Click project → Project Detail Page

**Project Detail Page:**

- Project info header (name, client name, status, deadline with color coding, hourly_rate, billable badge)
- Edit button
- Summary card: total tasks, todo/in-progress/done counts, total hours, billable amount
- Below: task list for this project
- Each task shows: title, status badge, priority badge, time spent, "start timer" button
- "Add Task" button → form with title, description, priority, estimated_hours
- Task status changeable via dropdown or click-to-cycle buttons

**Today's Tasks Page:**

- Three columns or sections: To Do, In Progress, Done
- Tasks show: title, project name (small text), priority badge, time spent
- "Add to today" button that opens task picker (search/filter from all tasks)
- Click task → expand or navigate to task detail
- Start/stop timer directly from this page
- Toggle task status directly from this page

**Task Timer Interaction:**

- "Start" button on a task → calls POST /api/time_entries, button changes to "Stop" with running clock (client-side timer counting up, syncs on stop)
- "Stop" button → calls PUT /api/time_entries/:id/stop, duration updates
- Only one timer can run per task (enforced by backend, UI should also prevent)
- If user starts timer on Task B while Task A has running timer, allow it (different tasks can have simultaneous timers — but one per task)

**Test Suite (Phase 4):**

- Test: Unauthenticated user redirected to login
- Test: Login with valid credentials redirects to dashboard
- Test: Register then login works end-to-end
- Test: Client CRUD works through UI (add, edit, delete, verify in list)
- Test: Project CRUD works through UI, client dropdown populated
- Test: Task CRUD works within project detail page
- Test: Timer start/stop updates displayed time
- Test: Today's page shows only marked tasks
- Test: Deadline color coding: overdue = red, approaching = yellow, future = default
- Test: Deleting client shows confirmation, removes from list after confirm
- Test: Navigation between pages works, back button works

**Verify:** All 10+ tests pass. Do not proceed until they do.

---

### PHASE 5: Professional UI/UX Polish

**Goal:** Transform the functional UI into something that looks and feels like a professional product. This phase is purely visual and interaction polish. No new features. No new API endpoints.

**Design System:**

- Define a color palette (pick ONE, stick to it):
  - Primary, secondary, success, warning, danger, neutral shades
  - Use CSS custom properties for all colors
- Typography: 2 fonts max. One for headings, one for body. Define sizes as a scale (xs, sm, base, lg, xl, 2xl)
- Spacing scale: 4px base (4, 8, 12, 16, 20, 24, 32, 40, 48, 64)
- Border radius: consistent (small: 4px, medium: 8px, large: 12px, pill: 999px)
- Shadows: 3 levels (sm, md, lg)
- Component states: default, hover, active, focus, disabled — define for every interactive element

**Layout Polish:**

- Sidebar: subtle background, active item has left border accent + background tint
- Cards: consistent padding, subtle shadow, hover lift effect
- Tables: alternating row shading, hover highlight, sticky header
- Forms: consistent label placement (above), input sizing, focus ring color, error state (red border + error message below)
- Empty states: illustration or icon + message + action button (e.g., "No clients yet. Add your first client.")

**Component Polish:**

- Status badges: colored pills (todo=gray, in-progress=blue, done=green, on-hold=yellow, completed=green, active=blue, inactive=gray)
- Priority badges: low=gray, medium=yellow, high=red
- Buttons: filled (primary action), outlined (secondary), ghost (tertiary) — consistent sizing
- Modals: centered, backdrop blur, smooth enter/exit animation (150ms ease-out)
- Delete confirmation: red accent, clear warning text
- Timer display: monospace font, pulsing dot when running, green when active

**Micro-interactions:**

- Button hover: slight scale (1.02) + shadow increase
- Status change: brief highlight flash
- Timer start: smooth transition to "running" state
- Page transitions: subtle fade (100ms)
- Form validation: inline error messages appear below field with slide-down
- Toast notifications for success/error actions (top-right, auto-dismiss after 3s)
  - "Client created successfully"
  - "Timer stopped — 1h 23m recorded"
  - "Project deleted"

**Dashboard Polish:**

- Summary cards in a row: each card has icon, number (large), label (small)
- Overdue projects: red-highlighted section
- Approaching deadlines: yellow-highlighted section
- Today's tasks: compact list with quick actions

**Responsive Behavior:**

- Desktop (>1024px): sidebar visible, multi-column where appropriate
- Tablet (768-1024px): sidebar collapsible, single column
- Mobile (<768px): no sidebar (hamburger menu), full-width cards, stacked layouts
- Timer page on mobile: large start/stop button, prominent time display

**Accessibility (Minimum):**

- All interactive elements reachable by keyboard (Tab order makes sense)
- Focus visible on all focusable elements
- Form labels properly associated with inputs
- Color is not the only indicator (overdue deadline has text + icon, not just red)
- Minimum touch target 44×44px on mobile

**Test Suite (Phase 5):**

- Test: All pages render without console errors
- Test: Responsive: check at 375px, 768px, 1024px, 1440px — no horizontal scroll, no overlapping elements
- Test: Keyboard: Tab through login form, all fields and button reachable
- Test: Empty states display correctly (delete all clients, verify empty state)
- Test: Toast appears and auto-dismisses on action
- Test: Modal opens and closes correctly, backdrop click closes
- Test: Timer display uses monospace font
- Test: Status badges have correct colors for all states

**Verify:** All 8+ tests pass. Do not proceed until they do.

---

### PHASE 6: Edge Cases, Error Handling, and Final Hardening

**Goal:** Make the app resilient. Handle every error gracefully. No raw stack traces in the UI. No dead-end states.

**Error Handling:**

- Every API error returns consistent format: `{ error: string, code: string, details?: any }`
- Network error: UI shows "Unable to connect. Check your internet connection."
- 401 expired token: auto-redirect to login with "Session expired" message
- 404 for deleted entity: redirect to parent list with "Item no longer exists" toast
- 500 server error: UI shows "Something went wrong. Please try again." with retry button
- Form submission error: show inline errors, do not clear the form

**Edge Cases to Handle:**

- Start timer on a task that already has a running timer → show message "Timer is already running"
- Delete a client that has projects with running timers → stop timers first, then delete (or block with message)
- Edit a project's client to a different client → allowed, warn if tasks have time entries
- Deadline in the past when creating a project → allow but show warning "This deadline is in the past"
- Very long task title or client name → truncate with ellipsis in lists, show full on hover/ detail
- Timer running when browser tab is in background → use timestamp-based calculation (not setInterval counting), sync on tab focus
- Multiple browser tabs → last stop wins, show warning if time seems unreasonable (>24h session)

**Data Integrity:**

- Add a `/api/health` endpoint that checks DB connection
- On app load, verify token validity, if invalid clear it and redirect to login
- Prevent double-submission of forms (disable button during request)

**Final Test Suite (Phase 6):**

- Test: 401 with expired token redirects to login
- Test: Delete client with running timers handles gracefully
- Test: Timer accuracy after tab backgrounding (mock Date.now behavior)
- Test: Double form submission prevented
- Test: Network error shows user-friendly message
- Test: All API errors return consistent format
- Test: Health endpoint returns 200
- Test: Empty form submission shows validation errors
- Test: Very long text truncates in list views

**Verify:** All 9+ tests pass. Run the COMPLETE test suite from Phase 1 through Phase 6. Everything must pass.

---

## 5. TECHNICAL REQUIREMENTS

### Backend

- Node.js with Express (or equivalent)
- PostgreSQL (recommended) or SQLite for simplicity
- Use an ORM or query builder (Prisma, Drizzle, or similar) — do not write raw SQL strings for queries
- JWT for auth (`jsonwebtoken` package)
- bcrypt for password hashing
- Environment variables for all secrets (JWT_SECRET, DATABASE_URL, etc.)
- Structured logging (console is fine for MVP, but structured JSON)

### Frontend

- React / Vue / Svelte (pick one, state your choice at the start)
- Client-side routing (React Router / Vue Router / etc.)
- HTTP client with interceptors for auth token injection and error handling
- State management: simple context/store, no Redux unless you have a reason
- No UI component library for Phase 4 (build basic components yourself to understand them)
- In Phase 5 you may optionally use a component library for faster polish (Radix, Headless UI, shadcn)

### Development

- `npm run dev` starts both backend and frontend concurrently
- `npm run test` runs all tests
- `npm run test:watch` runs tests in watch mode during development
- Hot reload for both frontend and backend during development

### Database Migrations

- Use migration files, not schema sync
- Every schema change is a new migration
- Seed script is separate from migrations

---

## 6. SECURITY CHECKLIST

- [ ] Passwords hashed with bcrypt (cost 12+)
- [ ] JWT secret from environment variable
- [ ] JWT expires (24h)
- [ ] No password_hash ever returned in API responses
- [ ] No user_id leakage (User A cannot guess User B's IDs — use UUIDs)
- [ ] Every query filters by user_id from token, not from request body
- [ ] SQL injection prevented (parameterized queries via ORM)
- [ ] XSS prevented (no `dangerouslySetInnerHTML` or equivalent)
- [ ] CORS configured to allow only your frontend origin
- [ ] Rate limiting on auth endpoints
- [ ] No sensitive data in URLs (no ?password=, no user_id in path for auth)
- [ ] Environment variables have sensible defaults for dev, required for prod

---

## 7. FILE STRUCTURE (Suggested)

```
/
├── package.json
├── .env.example
├── .gitignore
├── README.md
├── server/
│   ├── index.js
│   ├── config/
│   │   └── database.js
│   ├── middleware/
│   │   ├── auth.js
│   │   └── errorHandler.js
│   ├── routes/
│   │   ├── auth.js
│   │   ├── clients.js
│   │   ├── projects.js
│   │   ├── tasks.js
│   │   ├── timeEntries.js
│   │   └── dashboard.js
│   ├── models/
│   │   ├── User.js
│   │   ├── Client.js
│   │   ├── Project.js
│   │   ├── Task.js
│   │   └── TimeEntry.js
│   ├── migrations/
│   │   └── 001_initial_schema.sql
│   ├── seeds/
│   │   └── dev_seed.sql
│   └── utils/
│       └── helpers.js
├── client/
│   ├── index.html
│   ├── src/
│   │   ├── main.js
│   │   ├── App.js
│   │   ├── api/
│   │   │   ├── client.js
│   │   │   ├── auth.js
│   │   │   ├── clients.js
│   │   │   ├── projects.js
│   │   │   ├── tasks.js
│   │   │   └── dashboard.js
│   │   ├── components/
│   │   │   ├── Layout.js
│   │   │   ├── Sidebar.js
│   │   │   ├── StatusBadge.js
│   │   │   ├── PriorityBadge.js
│   │   │   ├── Timer.js
│   │   │   ├── Modal.js
│   │   │   ├── Toast.js
│   │   │   ├── EmptyState.js
│   │   │   └── ConfirmDialog.js
│   │   ├── pages/
│   │   │   ├── Login.js
│   │   │   ├── Register.js
│   │   │   ├── Dashboard.js
│   │   │   ├── Clients.js
│   │   │   ├── ClientDetail.js
│   │   │   ├── Projects.js
│   │   │   ├── ProjectDetail.js
│   │   │   └── Today.js
│   │   ├── hooks/
│   │   │   ├── useAuth.js
│   │   │   └── useTimer.js
│   │   └── styles/
│   │       ├── globals.css
│   │       └── variables.css
├── tests/
│   ├── phase1.crud.test.js
│   ├── phase2.auth.test.js
│   ├── phase3.business-logic.test.js
│   ├── phase4.ui.test.js
│   ├── phase5.polish.test.js
│   └── phase6.edge-cases.test.js
└── docker-compose.yml (optional, for PostgreSQL)
```

---

## 8. HOW TO USE THIS PRD — INSTRUCTIONS FOR THE CODING AGENT

1. **Read this entire PRD before writing any code.** Do not skim. Do not start coding after reading Phase 1.
2. **State your tech stack choices** at the beginning of your response: framework, ORM, database, test runner.
3. **Build Phase 1 completely.** Show me the database schema, the API endpoints, and the test results. Do not move to Phase 2 until I confirm Phase 1 is solid.
4. **When I say "proceed to Phase X," build that phase completely.** Show the code, show the tests passing.
5. **If you encounter a design decision not covered in this PRD:** make the simplest reasonable choice, note it in a comment, and move on. Do not ask me about font sizes or button colors.
6. **If you encounter a fundamental architectural conflict:** stop and explain the conflict and your proposed resolution. Wait for my input.
7. **Do not skip tests.** Do not say "tests will be added later." Tests are part of each phase's deliverable.
8. **Do not optimize prematurely.** The app should work correctly before it works fast. A query that takes 50ms is fine for an MVP. A query that returns wrong data is not.
9. **Commit after each phase.** Use clear commit messages: "Phase 1: Database foundation and CRUD API", "Phase 2: Authentication and security", etc.
10. **When all 6 phases are complete,** provide a summary: what was built, what tests exist and pass, what a user can do end-to-end, and what would be logical next steps for post-MVP.

---

## 9. SUCCESS CRITERIA — THE MVP IS DONE WHEN:

- [ ] A new user can register, log in, and stay logged in across page refreshes
- [ ] They can add 3 clients, each with 2 projects, each project with 3-5 tasks
- [ ] They can mark tasks for today and see them on the Today page
- [ ] They can start a timer on a task, see it counting, stop it, and see the accumulated time
- [ ] They can change task statuses and see the changes reflected everywhere
- [ ] They can view a project summary with correct billable amount
- [ ] Overdue deadlines are visually distinct and flagged on the dashboard
- [ ] They can delete a client and all associated data is removed
- [ ] All tests pass (40+ tests across all phases)
- [ ] No console errors during normal usage
- [ ] The app looks professional — not a prototype, not a tutorial output
