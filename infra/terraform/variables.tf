#############################################
# Input variables for vanity-numbers stack  #
#############################################

# Project name used in resource names and tags
variable "project_name" {
  type        = string
  description = "Logical project name used for naming and tagging"
  default     = "vanity-numbers"
}

# AWS region to deploy all resources
variable "region" {
  type        = string
  description = "AWS region to deploy into"
  default     = "us-west-2"
}

# Environment label for tags/metrics (e.g., dev/staging/prod)
variable "env" {
  type        = string
  description = "Environment label used for tagging and metrics dimensions"
  default     = "dev"
}

# Your Amazon Connect instance ID (not the ARN).
# Find it in the Amazon Connect console: the Instance ARN ends with /instance/<INSTANCE_ID>
variable "connect_instance_id" {
  type        = string
  description = "Amazon Connect Instance ID to associate the Lambda and create the contact flow"
}

# Toggle for deploying the bonus web app (S3 static site + API).
# If you prefer to always include it, leave default = true.
variable "enable_bonus_webapp" {
  type        = bool
  description = "Whether to provision the S3 static website for the bonus web app"
  default     = true
}