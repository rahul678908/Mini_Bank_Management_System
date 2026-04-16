# 🏦 Mini Banking System (Django + DRF)

## 📌 Objective

This project demonstrates a role-based banking system with:

* Customer & Employee roles
* Account management
* Loan handling
* JWT Authentication
* Celery for async tasks

---

## 🚀 Features

* 🔐 JWT Authentication (Login / Refresh)
* 👤 Role-based access (Customer, Employee, Manager)
* 💳 Bank Account Management
* 💰 Loan Management & Payments
* ⚡ Async Tasks using Celery + Redis
* 🛡️ Secure environment variables using `.env`

---

## 🛠️ Tech Stack

* Backend: Django, Django REST Framework
* Auth: JWT (`rest_framework_simplejwt`)
* Async: Celery + Redis
* Database: SQLite (default)

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd <project-folder>
```

---

### 2. Create virtual environment

```bash
python -m venv env
source env/bin/activate   # Linux/Mac
env\Scripts\activate      # Windows
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Setup Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Update values inside `.env`:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=db.sqlite3

CELERY_BROKER_URL=redis://127.0.0.1:6379/0

ACCESS_TOKEN_LIFETIME=2
REFRESH_TOKEN_LIFETIME=1
```

---

### 5. Run migrations

```bash
python manage.py migrate
```

---

### 6. Create superuser

```bash
python manage.py createsuperuser
```

---

### 7. Run the server

```bash
python manage.py runserver
```

---

## ⚡ Running Celery (Optional but Recommended)

Make sure Redis is running locally.

Start Celery worker:

```bash
celery -A core worker -l info
```

---

## 🔐 API Authentication

Uses JWT authentication:

* Login → Get access & refresh token
* Use token in headers:

```http
Authorization: Bearer <access_token>
```

---

## 👥 Roles & Permissions

| Role     | Permissions                             |
| -------- | --------------------------------------- |
| Customer | View own account, pay loans             |
| Employee | View all customers                      |
| Manager  | Full access (accounts, loans, interest) |

---

## 📂 Environment Variables

Sensitive data is managed using `.env`.

* `.env` → NOT pushed (secure)
* `.env.example` → provided for setup

---

## 💡 Notes for Interviewer

* Follows clean architecture & modular design
* Uses role-based permissions
* Handles exceptions properly
* Supports async processing via Celery
* Secure configuration using environment variables

---

## 📌 Future Improvements

* PostgreSQL integration
* Docker setup
* CI/CD pipeline
* Deployment (AWS / Render)

---

## 👨‍💻 Author

Rahul K
