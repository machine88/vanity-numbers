#############################################
# Input variables for vanity-numbers stack  #
#############################################

# Project name used in resource names and tags
variable "project_name" {
  type        = string
  description = "Logical project name used for naming and tagging"
  default     = "vanity-numbers"
}

# Environment label for tags/metrics (e.g., dev/staging/prod)
variable "env" {
  type        = string
  description = "Environment label used for tagging and metrics dimensions"
  default     = "dev"
}

# Toggle for deploying the bonus web app (S3 static site + API)
variable "enable_bonus_webapp" {
  type        = bool
  description = "Whether to provision the S3 static website for the bonus web app"
  default     = true
}

# AWS CLI/SDK profile
variable "aws_profile" {
  description = "AWS CLI/SDK profile name to use"
  type        = string
  default     = "AdministratorAccess-653464153304"
}

variable "region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-west-2"
}

variable "connect_instance_id" {
  description = "Amazon Connect instance ID"
  type        = string
}

variable "phone_number_id" {
  description = "Amazon Connect phone number ID"
  type        = string
}

variable "vanity_lambda_arn" {
  description = "ARN of the vanity Lambda function to be invoked by Connect"
  type        = string
}

variable "contact_flow_json_path" {
  description = "Relative path (from infra/terraform/) to the Connect flow JSON file."
  type        = string
  default     = "../../connect/vanity-contact-flow.json"
}