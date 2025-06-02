# User Management

A fastapi application to manage users - includes creating, updating, deleting and viewing of users and their information.

## Current Endpoints

1. GET /users - get all users
2. GET /users/{user_id} - get user details given an Id


## How to run application

1. Clone git repository to your local machine
    >git clone <https://github.com/sally-orig/FinalProject-Users.git> UserManagementProject
2. Go to UserManagementProject folder:
    >cd UserManagementProject
3. Build docker fastapi_users_image image
    >docker build -t fastapi_users_image .
4. Put up container
    >docker run -p 8085:8085 fastapi_users_image
