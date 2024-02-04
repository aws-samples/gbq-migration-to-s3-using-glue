terraform {
  backend "s3" {
  }
}

provider "aws" {
}

terraform {
  required_providers {
      aws = {
      source = "hashicorp/aws"
      version = "5.11.0"
    }
  }
}