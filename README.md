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

Note: Go to INSTRUCTIONS.md on how to run locally, on Docker, and on AWS Fargate.
