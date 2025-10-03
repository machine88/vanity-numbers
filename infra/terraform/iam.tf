#############################################
# IAM roles & policies for Lambda functions #
#############################################

# Trust policy so Lambda can assume these roles
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

########################
# Vanity Lambda (write)
########################
resource "aws_iam_role" "vanity_role" {
  name               = "${var.project_name}-vanity-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = local.common_tags
}

# Allow PutItem into our DynamoDB table
data "aws_iam_policy_document" "vanity_ddb_write" {
  statement {
    sid       = "DynamoPut"
    actions   = ["dynamodb:PutItem"]
    resources = [aws_dynamodb_table.vanity_calls.arn]
  }
}

resource "aws_iam_policy" "vanity_ddb_write" {
  name   = "${var.project_name}-vanity-ddb-write"
  policy = data.aws_iam_policy_document.vanity_ddb_write.json
  tags   = local.common_tags
}

# CloudWatch Logs basic permissions
data "aws_iam_policy_document" "logs_write" {
  statement {
    sid       = "LogsWrite"
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_policy" "logs_write" {
  name   = "${var.project_name}-logs-write"
  policy = data.aws_iam_policy_document.logs_write.json
  tags   = local.common_tags
}

# X-Ray permissions (tracing)
data "aws_iam_policy_document" "xray_write" {
  statement {
    sid       = "XRayWrite"
    actions   = ["xray:PutTraceSegments", "xray:PutTelemetryRecords"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "xray_write" {
  name   = "${var.project_name}-xray-write"
  policy = data.aws_iam_policy_document.xray_write.json
  tags   = local.common_tags
}

# Attach to Vanity role
resource "aws_iam_role_policy_attachment" "vanity_ddb_write_attach" {
  role       = aws_iam_role.vanity_role.name
  policy_arn = aws_iam_policy.vanity_ddb_write.arn
}
resource "aws_iam_role_policy_attachment" "vanity_logs_attach" {
  role       = aws_iam_role.vanity_role.name
  policy_arn = aws_iam_policy.logs_write.arn
}
resource "aws_iam_role_policy_attachment" "vanity_xray_attach" {
  role       = aws_iam_role.vanity_role.name
  policy_arn = aws_iam_policy.xray_write.arn
}

#######################
# API Lambda (read)
#######################
resource "aws_iam_role" "api_role" {
  name               = "${var.project_name}-api-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = local.common_tags
}

# Allow Scan/Query the DynamoDB table
data "aws_iam_policy_document" "api_ddb_read" {
  statement {
    sid       = "DynamoRead"
    actions   = ["dynamodb:Scan", "dynamodb:Query"]
    resources = [aws_dynamodb_table.vanity_calls.arn]
  }
}

resource "aws_iam_policy" "api_ddb_read" {
  name   = "${var.project_name}-api-ddb-read"
  policy = data.aws_iam_policy_document.api_ddb_read.json
  tags   = local.common_tags
}

# Attach to API role
resource "aws_iam_role_policy_attachment" "api_ddb_read_attach" {
  role       = aws_iam_role.api_role.name
  policy_arn = aws_iam_policy.api_ddb_read.arn
}
resource "aws_iam_role_policy_attachment" "api_logs_attach" {
  role       = aws_iam_role.api_role.name
  policy_arn = aws_iam_policy.logs_write.arn
}
resource "aws_iam_role_policy_attachment" "api_xray_attach" {
  role       = aws_iam_role.api_role.name
  policy_arn = aws_iam_policy.xray_write.arn
}
