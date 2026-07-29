# Infrastructure

The Terraform code begins with a deliberately small development environment. Future modules will provision networking, ECR, ECS Fargate, RDS PostgreSQL with pgvector, ElastiCache Redis, S3, IAM, secrets and observability.

Run locally:

```bash
cd environments/dev
terraform init
terraform fmt -check
terraform validate
terraform plan
```
