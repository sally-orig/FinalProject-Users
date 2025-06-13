# 👥 User Management API

A FastAPI-based application to manage users — supports creating, updating, deleting, and retrieving user information.

---

## 🚀 Features

- Retrieve all users (Supports pagination and status filters)
- Retrieve user by ID
- Register new user
- Generate token after successful user log in
- Verify token
- Uses SQLite with Alembic for migrations
- Dockerized for easy deployment

---

## 📚 API Endpoints

| Method | Endpoint           | Description              |
|--------|--------------------|--------------------------|
| POST   | `/token`           | Generate token for auth  |
| POST   | `/token/verify`    | Verify token             |
| GET    | `/users`           | Retrieve all users       |
| GET    | `/users/{user_id}` | Get user by ID           |
| POST   | `/users/register`  | Register a new user      |

> You can explore and test these endpoints via the **Swagger UI** at [http://localhost:8085/docs](http://localhost:8085/docs) once the app is running.

---

Note: Go to INSTRUCTIONS.md on how to run locally, on Docker, and on AWS Fargate.
