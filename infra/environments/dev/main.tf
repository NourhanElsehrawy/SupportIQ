terraform {
  required_version = ">= 1.8.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "SupportIQ"
      Environment = "dev"
      ManagedBy   = "Terraform"
    }
  }
}

# Intentionally minimal. Networking, ECR, ECS, RDS, Redis and S3
# will be added as separate reviewed modules in later milestones.
