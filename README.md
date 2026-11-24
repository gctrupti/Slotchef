<div align="center">

# 🍳 SlotChef

### Intelligent In-Home Culinary Operations & Exact Discrete Scheduling Platform

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Google OR-Tools](https://img.shields.io/badge/Google_OR--Tools-CP--SAT-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://developers.google.com/optimization)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Tests](https://img.shields.io/badge/Tests-80%20Passing%20(100%25)-success?style=for-the-badge)](tests/)

<p align="center">
  <b>A production-grade engineering platform that coordinates trusted, in-home cooking visits for residential apartment communities with mathematical constraint optimization.</b>
</p>

[Key Features](#-key-features) •
[Architecture](#-system-architecture) •
[Tech Stack](#-tech-stack) •
[Quick Start](#-quick-start-guide) •
[Scheduling Engine](#-or-tools-scheduling-engine) •
[API Docs](#-api-documentation) •
[Test Suite](#-automated-testing--verification)

</div>

---

## 📖 Overview

**SlotChef** (formerly *SharedCook*) solves the urban in-home dining challenge. Traditional home cook arrangements suffer from high cook turnover, exhausting commutes, overlapping bookings, and miscommunicated dietary requirements.

SlotChef introduces **hyper-local society clustering**:
- Cooks work within designated gated residential communities (e.g., *Green Meadows Residency*, *Palm Heights*), walking between apartment towers rather than traveling across the city.
- Meal slots (**Breakfast**, **Lunch**, and **Dinner**) are booked by households and dynamically scheduled using **Google OR-Tools CP-SAT constraint programming**.
- **PostgreSQL GiST exclusion constraints** guarantee zero double-booking race conditions at the database engine level.
- Saved **dietary vaults** (spice levels, oil preferences, Jain/Keto diets) are automatically routed to cook mobile cockpits before every visit.

---

## ✨ Key Features

### 🎯 Mathematical Constraint Scheduling (Google OR-Tools CP-SAT)
- Replaces naive greedy algorithms with exact constraint satisfaction.
- Enforces strict hard constraints: skill prerequisites, cook working windows, mandatory breaks, approved leaves, and **directional 5-minute travel buffers** between apartment flats.
- Optimizes multi-objective soft goals: minimizing household wait time, balancing cook workload equity, and rewarding cook-to-household familiarity.

### 🛡️ Physical Zero Double-Booking Guarantee
- Leverages PostgreSQL's `btree_gist` extension with an `EXCLUDE USING gist` constraint on `(cook_id WITH =, tstzrange(start_time, end_time, '[)') WITH &&)`.
- Concurrent overlapping booking attempts fail at the database engine level with an `IntegrityError`, eliminating race conditions under high traffic.

### 🚨 Dynamic Incident Handling & Backup Cook Re-Optimization
- When an emergency or transit delay occurs, the system flags the assignment, re-optimizes remaining unfulfilled visits for that society, and dispatches an eligible backup cook without downstream collisions.
- Every plan transition increments the version (`v1` → `v2`) while preserving displaced bookings (`STATUS_REPLACED`) for strict audit compliance.

### 🔐 3-Tier Identity & Unified RBAC
- Dedicated, isolated workflows for **Households**, **Cook Partners**, and **Society Administrators**.
- Sequential dual-channel (SMS + Email) registration OTP verification.
- Dual-identifier password login (Email or Mobile) with a 5-attempt / 15-minute brute-force lockout.
- Time-based step-up MFA for administrative operations.

### 🦺 In-Field Visit Safety & Security Gate Passes
- 4-digit society gate pass code for swift apartment security clearance.
- GPS-verified arrival check-in and completion workflow (*Dispatched → Gate Pass Verified → Arrived at Flat → Cooking Started → Completed*).
- Active visit location pings, automated overdue visit detection, and one-tap emergency SOS alarms mapped to the **India 112 schema**.

---

## 🏛️ System Architecture

```text
                               +-------------------------------------------------------+
                               |                 Client Applications                   |
                               |    React 18 + Vite Web App  /  Mobile Client (Flutter)|
                               +-------------------------------------------------------+
                                                           |
                                                           | HTTPS / REST v1 (JWT Auth)
                                                           v
+----------------------------------------------------------------------------------------------------------------------+
|                                             SlotChef Django 6 Monolith                                               |
|                                                                                                                      |
|   +--------------------+  +--------------------+  +--------------------+  +--------------------+  +----------------+ |
|   |   apps.identity    |  |  apps.communities  |  |   apps.households  |  |     apps.cooks     |  |  apps.bookings | |
|   +--------------------+  +--------------------+  +--------------------+  +--------------------+  +----------------+ |
|   +--------------------+  +--------------------+  +--------------------+  +--------------------+  +----------------+ |
|   |  apps.scheduling   |  |    apps.visits     |  |    apps.finance    |  |     apps.audit     |  | apps.operations| |
|   +--------------------+  +--------------------+  +--------------------+  +--------------------+  +----------------+ |
|                                                           |                                                          |
|                                               Scheduling Orchestrator                                                |
+-----------------------------------------------------------|----------------------------------------------------------+
                               | (Domain Snapshot)          ^ (Optimized Plan)
                               v                            |
+----------------------------------------------------------------------------------------------------------------------+
|                                     Google OR-Tools CP-SAT Solver Package                                            |
|                                            (slotchef_optimizer)                                                      |
|   • Integer Discrete Minute-of-Day Domain [0..1440]       • AddNoOverlap Interval Variables                          |
|   • Working Shift Windows & Protected Break Collisions   • Directional 5-Min Transition Travel Buffers              |
|   • Daily Workload Minute & Visit Caps                   • Multi-Objective Balanced Weighted Penalty Function        |
+----------------------------------------------------------------------------------------------------------------------+
                                                           |
                                                           | Engine Transactions & GiST Lock
                                                           v
+----------------------------------------------------------------------------------------------------------------------+
|                                         Authoritative Cloud PostgreSQL 17                                            |
|   • btree_gist PostgreSQL Extension                      • EXCLUDE USING gist (cook_id WITH =, tstzrange WITH &&)   |
|   • Row-Level Security (RLS) Active                      • Immutable Schedule Plan Versioning & Audit Logs           |
+----------------------------------------------------------------------------------------------------------------------+
```

---

## 💻 Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.13, Django 6, DRF | Modular monolith architecture, domain entities, transaction orchestration |
| **Optimization Engine** | Google OR-Tools CP-SAT | Discrete constraint programming & multi-objective schedule optimization |
| **Database** | PostgreSQL 17 (Supabase / Local) | Authoritative persistence with `btree_gist` GiST exclusion constraints |
| **Cache & Task Queue** | Redis, Celery | Idempotency caching (24-hour TTL), async task dispatching |
| **Frontend App** | React 18, Vite 6, TypeScript | Consumer & operational presentation layer |
| **Styling & Components**| Tailwind CSS, shadcn/ui | Modern, responsive, accessible design system |
| **Icons & Visuals** | Lucide React, FullCalendar, Recharts | Interactive calendars, data visualization, and iconography |
| **API Documentation** | OpenAPI 3.0 via `drf-spectacular` | Interactive Swagger UI (`/api/v1/docs/`) and Redoc |
| **Testing & Quality** | Pytest, Pytest-Django, Ruff | 80 automated unit & integration tests, static code analysis |

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.13+** (`python --version`)
- **Node.js 18+** & **npm** (`node --version`)
- **Git**
- Access to **PostgreSQL** (or Supabase Cloud PostgreSQL)

### 1. Clone the Repository
```bash
git clone https://github.com/gctrupti/Slotchef.git
cd Slotchef
```

### 2. Configure Environment Variables
Copy the template configuration to `.env`:
```bash
cp .env.example .env
```
*(On Windows PowerShell: `Copy-Item .env.example .env`)*

Configure your database connection in `.env`:
```env
DJANGO_SECRET_KEY=your-secure-random-secret-key
DJANGO_DEBUG=true
DATABASE_URL=postgresql://postgres:password@localhost:5432/slotchef?sslmode=prefer
REDIS_URL=redis://localhost:6379/0
CELERY_TASK_ALWAYS_EAGER=true
```

### 3. Backend Setup
```bash
# Create and activate virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -e optimizer

# Run database migrations
cd backend
python manage.py check
python manage.py migrate

# Start development server (Port 8000)
python manage.py runserver 127.0.0.1:8000
```

### 4. Frontend Setup
In a new terminal window:
```bash
cd frontend

# Install npm packages
npm install

# Start Vite dev server (Port 3000)
npm run dev
```

Visit the applications in your browser:
- **Frontend App:** [http://localhost:3000](http://localhost:3000)
- **Backend API Root:** [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- **Swagger UI Documentation:** [http://127.0.0.1:8000/api/v1/docs/](http://127.0.0.1:8000/api/v1/docs/)

---

## 🐳 Docker Deployment

To spin up the entire backend stack (API + Celery + Redis + local PostgreSQL) using Docker Compose:

```bash
# Start all services
docker compose --profile local-db up --build

# Run migrations inside the container
docker compose exec backend python manage.py migrate
```

---

## 🧠 OR-Tools Scheduling Engine

The engine mathematically models scheduling as a constraint satisfaction problem in `optimizer/slotchef_optimizer`:

1. **Time Domain:** All minutes within a day are mapped to integer values $[0, 1440]$.
2. **Interval Decision Variables:** For every booking $b$ and eligible cook $c$:
   $$interval_{b,c} = \text{NewOptionalIntervalVar}(start_{b,c}, duration_b, end_{b,c}, presence_{b,c})$$
3. **Hard Non-Overlap:** Intervals assigned to a single cook cannot overlap:
   $$\text{model.AddNoOverlap}([interval_1, interval_2, \dots])$$
4. **Directional Transition Buffer:** If cook $c$ completes flat $i$ and proceeds to flat $j$:
   $$start_j \ge end_i + 5 \text{ minutes}$$
5. **Multi-Objective Minimization:**
   $$\min \sum_{b, c} \Big( w_{\text{start}} \cdot |start_{b,c} - preferred\_start_b| + w_{\text{workload}} \cdot (workload_c - \overline{workload})^2 - w_{\text{continuity}} \cdot FamiliarityBonus(b, c) \Big)$$

---

## 📡 API Documentation

Interactive OpenAPI 3.0 documentation is served at `/api/v1/docs/`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register new Resident or Cook with sequential OTP verification |
| `POST` | `/api/v1/auth/login` | Dual-identifier (email/phone) password login with brute-force protection |
| `POST` | `/api/v1/auth/admin/mfa-verify` | Step-up MFA challenge for administrative operations |
| `POST` | `/api/v1/households/<id>/bookings` | Create a booking request (Triggers CP-SAT solver & creates assignment) |
| `GET` | `/api/v1/cooks/me/schedule?date=YYYY-MM-DD` | Fetch cook's daily assigned visit roster |
| `POST` | `/api/v1/assignments/<id>/check-in` | Cook GPS-verified arrival check-in at flat |
| `POST` | `/api/v1/assignments/<id>/start` | Start cooking session (Transitions booking to `IN_PROGRESS`) |
| `POST` | `/api/v1/assignments/<id>/complete` | Complete cooking session & clean-up confirmation |
| `POST` | `/api/v1/assignments/<id>/report-incident` | Report in-field emergency & trigger backup cook re-optimization |
| `GET` | `/api/v1/pricing/estimate` | Compute dynamic pricing breakdown with package discount snapshots |

---

## 🧪 Automated Testing & Verification

The test suite covers unit logic, concurrency isolation, CP-SAT optimizer scenarios, and integration workflows:

```bash
# High-speed offline SQLite test run (~28s)
$env:SLOTCHEF_UNIT_TEST_SQLITE="1"
pytest -v

# Live PostgreSQL test run (Validates GiST exclusion constraints & RLS)
pytest -v

# Code linting and formatting verification
ruff check backend optimizer
```

**Verification Results:**
- **80 automated tests passing** (100% pass rate).
- **20 deterministic scenarios verified** covering skill mismatches, overlapping requests, break collisions, transition buffers, and concurrent double-booking attempts.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

<div align="center">
  <sub>Built with ❤️ for modern residential apartment communities.</sub>
</div>
