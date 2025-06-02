# 👥 User Management API

A FastAPI-based application to manage users — supports creating, updating, deleting, and retrieving user information.

---

## 🚀 Features

- Retrieve all users
- Retrieve user by ID
- Supports pagination and status filters
- Uses SQLite with Alembic for migrations
- Dockerized for easy deployment

---

## 📚 API Endpoints

| Method | Endpoint           | Description              |
|--------|--------------------|--------------------------|
| GET    | `/users`           | Retrieve all users       |
| GET    | `/users/{user_id}` | Get user by ID           |

> You can explore and test these endpoints via the **Swagger UI** at [http://localhost:8085/docs](http://localhost:8085/docs) once the app is running.

---

## 🐳 How to Run Using Docker

### 1. Clone the Repository

```bash
git clone https://github.com/sally-orig/FinalProject-Users.git UserManagementProject

cd UserManagementProject
```

### 2. Build Docker Image

```bash
docker build -t fastapi_users_image .
```

### 3. Run container

```bash
docker run -p 8085:8085 fastapi_users_image
```
