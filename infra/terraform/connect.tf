############################################
# Connect: manage the existing flow by ID
############################################
locals {
  contact_flow_json = "${path.module}/${var.contact_flow_json_path}"
}

# IMPORTANT: we render your JSON and inject the Lambda ARN
resource "aws_connect_contact_flow" "verify_flow" {
  name        = "vanity-numbers-flow-tf"
  description = "Invoke Lambda to get vanity options and speak top 3"
  instance_id = var.connect_instance_id
  type        = "CONTACT_FLOW"
  region      = var.region

  # however you currently set content (file/templatefile/etc.)
  content = templatefile(local.contact_flow_json, {
    lambda_arn = var.vanity_lambda_arn
  })

  # 👇 add this to prevent Terraform from updating the JSON in Connect
  lifecycle {
    ignore_changes = [content]
  }
}

# Allow the Connect instance to invoke the Lambda
resource "aws_lambda_permission" "allow_connect_invoke" {
  statement_id  = "AllowExecutionFromAmazonConnect"
  action        = "lambda:InvokeFunction"
  function_name = var.vanity_lambda_arn
  principal     = "connect.amazonaws.com"
  source_arn    = "arn:aws:connect:${var.region}:${data.aws_caller_identity.current.account_id}:instance/${var.connect_instance_id}"
}

# Associate the Lambda function with the Connect instance (required once per instance)
resource "aws_connect_lambda_function_association" "vanity_assoc" {
  instance_id  = var.connect_instance_id
  function_arn = var.vanity_lambda_arn
  region       = var.region
}

# Point your phone number at this flow
resource "aws_connect_phone_number_contact_flow_association" "verify_number_assoc" {
  instance_id     = var.connect_instance_id
  phone_number_id = var.phone_number_id
  contact_flow_id = aws_connect_contact_flow.verify_flow.contact_flow_id
  region          = var.region
}
