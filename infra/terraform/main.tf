#############################################
# Terraform entrypoint for infra deployment #
#############################################

terraform {
  # Require a reasonably recent Terraform
  required_version = ">= 1.6.0"

  # Declare providers used in this stack
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    # AWS Cloud Control provider — used for Amazon Connect contact flow resource
    awscc = {
      source  = "hashicorp/awscc"
      version = ">= 1.0"
    }
  }
}

######################
# Provider configs   #
######################

# Primary AWS provider (Lambda, DynamoDB, API Gateway, S3, IAM, etc.)
provider "aws" {
  region = var.region
}

# AWS Cloud Control provider (broad coverage for some services like Connect)
provider "awscc" {
  region = var.region
}

#############################
# Identity & shared locals  #
#############################

# Your AWS account identity (used for ARNs, tags, outputs)
data "aws_caller_identity" "current" {}

# Shared computed values available to other .tf files in this module
locals {
  account_id = data.aws_caller_identity.current.account_id

  # Common tags applied to resources (extend as you like)
  common_tags = {
    Project = var.project_name
    Env     = var.env
    Owner   = "vanity-numbers"
  }
}

#############################
# (Nothing else lives here) #
# Other resources are split #
# into dedicated .tf files. #
#############################
