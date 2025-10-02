#############################################
# Useful outputs for vanity-numbers stack   #
#############################################

# Echo basics for convenience
output "region" {
  description = "AWS region used for this deployment"
  value       = var.region
}

output "account_id" {
  description = "AWS account ID this stack deployed into"
  value       = local.account_id
}

# DynamoDB
output "ddb_table_name" {
  description = "DynamoDB table storing caller events and vanity candidates"
  value       = aws_dynamodb_table.vanity_calls.name
}

# Vanity Lambda
output "vanity_lambda_name" {
  description = "Deployed vanity Lambda function name"
  value       = aws_lambda_function.vanity.function_name
}

output "vanity_lambda_arn" {
  description = "Deployed vanity Lambda function ARN"
  value       = aws_lambda_function.vanity.arn
}

# API (bonus)
output "api_base_url" {
  description = "HTTP API base URL (append /last5 for data)"
  value       = aws_apigatewayv2_api.http.api_endpoint
  # If you disable the bonus web app in the future,
  # you may want to conditionally create API resources too.
}

output "cloudfront_url" {
  description = "Public HTTPS URL for the static web app"
  value       = try(aws_cloudfront_distribution.web[0].domain_name, null)
}

# Amazon Connect
output "connect_instance_arn" {
  description = "Amazon Connect instance ARN derived from inputs"
  value       = "arn:aws:connect:${var.region}:${local.account_id}:instance/${var.connect_instance_id}"
}

output "contact_flow_id" {
  description = "ID of the created Amazon Connect Contact Flow"
  value       = aws_connect_contact_flow.vanity_flow.contact_flow_id
}

# CloudFront distribution ID (useful for manual invalidations)
output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for the static site"
  value       = try(aws_cloudfront_distribution.web[0].id, null)
}