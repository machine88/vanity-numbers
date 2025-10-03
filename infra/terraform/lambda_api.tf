# API Lambda: returns the last 5 callers for the web app
resource "aws_lambda_function" "api_last5" {
  function_name = "${var.project_name}-api-last5"
  role          = aws_iam_role.api_role.arn
  filename      = "./../build/lambda_api.zip"

  # FIX: the file in the zip is at the root (api_handler.py)
  handler       = "api_handler.handler"

  runtime       = "python3.12"
  architectures = ["arm64"]
  timeout       = 5
  memory_size   = 256

  source_code_hash = filebase64sha256("${path.module}/../build/lambda_api.zip")

  environment {
    variables = {
      DDB_TABLE = aws_dynamodb_table.vanity_calls.name
      ENV       = var.env
    }
  }

  tracing_config { mode = "Active" }
}

resource "aws_cloudwatch_log_group" "api_last5" {
  name              = "/aws/lambda/${aws_lambda_function.api_last5.function_name}"
  retention_in_days = 14
  tags              = local.common_tags
}