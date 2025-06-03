output "ecr_repo_url" {
  value = aws_ecr_repository.fastapi.repository_url
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.fastapi.name
}
