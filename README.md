# Student Management System

A RESTful API backend built with **FastAPI** for managing university students, featuring JWT authentication, role-based access control, Redis caching, structured logging, and a monitoring dashboard.

---

## 👥 Team Members

| # | Name | Role |
|---|------|------|
| 1 | Member 1 | JWT & Authentication |
| 2 | Member 2 | Student CRUD & Database |
| 3 | Member 3 | Redis Caching |
| 4 | Member 4 | Logging & Monitoring Dashboard |
| 5 | Member 5 | API Testing |
| 6 | Member 6 | Frontend Integration |

---

## 📋 Features

- ✅ User registration & login with JWT tokens
- ✅ Role-based access control (Admin / Student)
- ✅ Full CRUD operations for students
- ✅ Advanced filtering by department and GPA
- ✅ Pagination support
- ✅ Students can only access their own profile
- ✅ Audit logging for all update operations
- ✅ Redis caching with Cache-Aside pattern
- ✅ Structured logging with Loguru
- ✅ Monitoring dashboard (metrics & logs viewer)
- ✅ Prometheus metrics endpoint (`/metrics`)
- ✅ Frontend UI (`/ui`)

---

## 🗂️ Project Structure

```
student-management-system/
├── app/
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Settings & environment variables
│   ├── database.py           # SQLAlchemy + Redis setup
│   ├── dependencies.py       # JWT token validation & role guards
│   ├── logger.py             # Loguru structured logging
│   ├── middleware.py         # Request/response logging middleware
│   ├── models/
│   │   ├── user.py           # User ORM model
│   │   ├── student.py        # Student ORM model
│   │   └── audit_log.py      # Audit log ORM model
│   ├── schemas/
│   │   ├── user.py           # Pydantic schemas for users
│   │   └── student.py        # Pydantic schemas for students
│   ├── routes/
│   │   ├── auth.py           # /auth/register, /auth/login
│   │   ├── students.py       # /students/* CRUD endpoints
│   │   └── monitoring.py     # /monitoring/* dashboard endpoints
│   └── services/
│       ├── auth_service.py   # Password hashing, token creation
│       └── student_service.py# Student business logic + caching
├── tests/
│   ├── conftest.py           # Pytest fixtures
│   ├── test_auth.py          # Authentication tests
│   └── test_students.py      # Student CRUD & role tests
├── frontend.html             # Single-page frontend UI
├── .env.example              # Example environment variables
├── requirements.txt          # Python dependencies
└── README.md
```

---

## ⚙️ Setup Instructions

### Prerequisites

- Python 3.9+
- Redis server running on `localhost:6379`

### 1. Clone the repository

```bash
git clone https://github.com/your-team/student-management-system.git
cd student-management-system
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set your values:

```env
DATABASE_URL=sqlite:///./student_management.db
SECRET_KEY=your-strong-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Start Redis

```bash
# Linux/Mac
redis-server

# Windows (WSL or Redis for Windows)
redis-server
```

### 6. Run the application

```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

---

## 🌐 Available Endpoints

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/` | Public | Welcome message |
| GET | `/health` | Public | Health check |
| GET | `/ui` | Public | Frontend UI |
| GET | `/metrics` | Public | Prometheus metrics |
| GET | `/monitoring/dashboard` | Public | Monitoring dashboard UI |
| GET | `/monitoring/stats` | Public | API stats (JSON) |
| POST | `/auth/register` | Public | Register new user |
| POST | `/auth/login` | Public | Login & get JWT token |
| GET | `/students/` | Admin | Get all students (with filters) |
| POST | `/students/` | Admin | Create new student |
| GET | `/students/{id}` | Admin | Get student by ID |
| DELETE | `/students/{id}` | Admin | Delete student |
| GET | `/students/me` | Student | Get own profile |
| PUT | `/students/me` | Student | Update own profile |

---

## 🔐 Authentication

All protected endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

Get a token by calling `POST /auth/login` with your username and password.

---

## 🐳 Docker

### Run with Docker Compose (Recommended)

```bash
# Build and start all services (app + Redis)
docker-compose up --build

# Run in background
docker-compose up --build -d

# Stop all services
docker-compose down
```

The app will be available at: `http://localhost:8000`

### Services

| Service | Port | Description |
|---------|------|-------------|
| app | 8000 | FastAPI application |
| redis | 6379 | Redis cache |

### Build image only

```bash
docker build -t student-management-system .
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📊 Monitoring

- **Prometheus Metrics:** `http://localhost:8000/metrics`
- **Monitoring Dashboard:** `http://localhost:8000/monitoring/dashboard`
- **Stats API:** `http://localhost:8000/monitoring/stats`
- **Logs:** stored in `logs/app.log` and `logs/audit.log`

---

## 👤 Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full CRUD on all students, view all records |
| **Student** | View and partially update own profile only |
