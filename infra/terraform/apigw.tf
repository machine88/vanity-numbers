resource "aws_apigatewayv2_api" "http" {
  name          = "${var.project_name}-http"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api_last5.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "get_last5" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "GET /last5"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# IMPORTANT: stage
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "allow_apigw_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_last5.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

# apigw.tf
resource "aws_apigatewayv2_route" "options_last5" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "OPTIONS /last5"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}