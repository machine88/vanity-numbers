##############################
# Amazon Connect: Contact Flow
##############################

# NOTE: This resource ONLY creates a contact flow from a known-good JSON file.
# Do not add data sources or locals here to avoid duplicate definitions.

resource "aws_connect_contact_flow" "vanity_flow" {
  name        = "${var.project_name}-flow-from-file"
  description = "Contact flow created from a known-good JSON file"
  instance_id     = var.connect_instance_id
  type        = "CONTACT_FLOW"

  # Use the JSON you exported: infra/terraform/contact_flow_valid.json
  content = file("${path.module}/contact_flow_valid.json")

  tags = {
    Project = var.project_name
    Env     = var.env
  }
}

resource "aws_connect_phone_number" "vanity_number" {
  # REQUIRED for the resource schema
  target_arn   = "arn:aws:connect:${var.region}:${data.aws_caller_identity.current.account_id}:instance/${var.connect_instance_id}"
  type         = "DID"
  country_code = "US"

  # DO NOT set phone_number here — it’s computed for imported numbers
}

resource "aws_connect_phone_number_contact_flow_association" "vanity_assoc" {
  instance_id     = var.connect_instance_id
  phone_number_id = aws_connect_phone_number.vanity_number.id
  contact_flow_id = split(":", aws_connect_contact_flow.vanity_flow.id)[1]
}

resource "aws_connect_lambda_function_association" "vanity_assoc" {
  instance_id  = var.connect_instance_id
  function_arn = aws_lambda_function.vanity.arn
  region       = var.region
}