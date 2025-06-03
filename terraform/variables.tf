variable "region" {
  default = "us-east-1"
}

variable "ecr_repo_name" {
  default = "fastapi-user"
}

variable "ecs_cluster_name" {
  default = "fastapi-user-cluster"
}

variable "ecs_service_name" {
  default = "fastapi-user-service"
}

variable "task_family" {
  default = "fastapi-user-task"
}
