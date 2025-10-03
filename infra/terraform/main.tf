#############################################
# Terraform entrypoint for infra deployment #
#############################################

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    awscc = {
      source  = "hashicorp/awscc"
      version = ">= 1.0"
    }
  }
}

######################
# Provider configs   #
######################

provider "aws" {
  profile = var.aws_profile
  region  = var.region
}

# (awscc not strictly required for this flow, but harmless to keep)
provider "awscc" {
  region = var.region
}

#############################
# Identity & shared locals  #
#############################

data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id

  common_tags = {
    Project = var.project_name
    Env     = var.env
    Owner   = "vanity-numbers"
  }
}