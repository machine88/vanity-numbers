########################################################
# Vanity Lambda function (invoked by Amazon Connect)   #
########################################################

resource "aws_lambda_function" "vanity" {
  function_name = "${var.project_name}-vanity"
  role          = aws_iam_role.vanity_role.arn
  filename      = "./../build/lambda_vanity.zip"
  handler       = "app.handler.handler"
  runtime       = "python3.12"
  architectures = ["arm64"]
  timeout       = 5
  memory_size   = 256

  # Built artifact produced by your build step
  source_code_hash = filebase64sha256("${path.module}/../build/lambda_vanity.zip")

  environment {
    variables = {
      DDB_TABLE = aws_dynamodb_table.vanity_calls.name
      ENV       = var.env
    }
  }

  # Turn on AWS X-Ray tracing for this function
  tracing_config {
    mode = "Active"
  }

  # Optional: set log retention to keep costs/noise in check (14 days)
  # resource "aws_cloudwatch_log_group" must be separate if you want retention control.
  # If you don't define it, Lambda auto-creates a log group with infinite retention.
}

# (Optional) Manage the log group explicitly to control retention
resource "aws_cloudwatch_log_group" "vanity" {
  name              = "/aws/lambda/${aws_lambda_function.vanity.function_name}"
  retention_in_days = 14
  tags              = local.common_tags
}

########################################################
# Allow Amazon Connect to invoke the vanity Lambda      #
########################################################

# Permits *your* Connect instance to call this function.
resource "aws_lambda_permission" "allow_connect_invoke" {
  statement_id  = "AllowExecutionFromAmazonConnect"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.vanity.function_name
  principal     = "connect.amazonaws.com"
  source_arn    = "arn:aws:connect:${var.region}:${local.account_id}:instance/${var.connect_instance_id}"
}