########################################################
# Vanity Lambda function (invoked by Amazon Connect)   #
########################################################

# Reuse the role & DDB table already declared in iam.tf and dynamodb.tf:
# - aws_iam_role.vanity_role
# - aws_dynamodb_table.vanity_calls

resource "aws_lambda_function" "vanity" {
  function_name = "${var.project_name}-vanity"
  role          = aws_iam_role.vanity_role.arn


  # built artifact produced by your build step
  filename         = "${path.module}/../build/lambda_vanity.zip"
  handler          = "app.handler.handler"
  runtime          = "python3.12"
  architectures    = ["arm64"]
  timeout          = 5
  memory_size      = 256
  source_code_hash = filebase64sha256("${path.module}/../build/lambda_vanity.zip")

  environment {
    variables = {
      DDB_TABLE = aws_dynamodb_table.vanity_calls.name
      ENV       = var.env
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "vanity" {
  name              = "/aws/lambda/${aws_lambda_function.vanity.function_name}"
  retention_in_days = 14
  tags              = local.common_tags
}

