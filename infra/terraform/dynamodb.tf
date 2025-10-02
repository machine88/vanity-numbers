#############################################
# DynamoDB table for call vanity records    #
#############################################

resource "aws_dynamodb_table" "vanity_calls" {
  name         = "${var.project_name}-VanityCalls"
  billing_mode = "PAY_PER_REQUEST"

  # Primary key: caller partition, time-ordered sort key
  hash_key  = "pk"
  range_key = "sk"

  attribute {
    name = "pk"
    type = "S"
  }
  attribute {
    name = "sk"
    type = "S"
  }

  # Point-in-time recovery (optional, commented to keep costs minimal for demo)
  # point_in_time_recovery {
  #   enabled = true
  # }

  tags = local.common_tags
}