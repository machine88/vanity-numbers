/***********************
 * Outputs
 ***********************/

# Phone number this flow is attached to
output "phone_number_id" {
  description = "ID of the Connect phone number associated to the flow"
  value       = var.phone_number_id
}

# Instance for convenience
output "connect_instance_id" {
  description = "Amazon Connect instance ID"
  value       = var.connect_instance_id
}

# Expose the Lambda ARN from the resource (not from a var)
output "vanity_lambda_arn" {
  description = "Lambda used by the flow"
  value       = aws_lambda_function.vanity.arn
}

output "verify_contact_flow_id" {
  value       = aws_connect_contact_flow.verify_flow.contact_flow_id
  description = "Contact Flow ID"
}

output "verify_contact_flow_arn" {
  value       = aws_connect_contact_flow.verify_flow.arn
  description = "Contact Flow ARN"
}