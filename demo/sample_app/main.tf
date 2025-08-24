data "aws_region" "current" {}

data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "demo_web_service.zip"

  source {
    content  = file("${path.module}/lambda_function.py")
    filename = "lambda_function.py"
  }
}

locals {
  lambda_name = "noop-demo-web-service"
  api_name    = "noop-demo-api"
}

resource "aws_cloudwatch_log_group" "main" {
  name              = "/aws/lambda/${local.lambda_name}"
  retention_in_days = 14
}

resource "aws_lambda_function" "main" {
  filename         = "demo_web_service.zip"
  function_name    = local.lambda_name
  role             = aws_iam_role.demo_lambda_execution_role.arn
  handler          = "lambda_function.handler"
  runtime          = "python3.13"
  timeout          = 30
  memory_size      = 256
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }

  depends_on = [aws_cloudwatch_log_group.main]
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "main" {
  name        = local.api_name
  description = "Demo API for noop testing"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# API Gateway Resource (catch-all proxy)
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "{proxy+}"
}

# API Gateway Method for root
resource "aws_api_gateway_method" "root" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_rest_api.main.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
}

# API Gateway Method for proxy
resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

# API Gateway Integration for root
resource "aws_api_gateway_integration" "root" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_rest_api.main.root_resource_id
  http_method             = aws_api_gateway_method.root.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.main.invoke_arn
}

# API Gateway Integration for proxy
resource "aws_api_gateway_integration" "proxy" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.proxy.id
  http_method             = aws_api_gateway_method.proxy.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.main.invoke_arn
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "main" {
  depends_on = [
    aws_api_gateway_integration.root,
    aws_api_gateway_integration.proxy,
  ]

  rest_api_id = aws_api_gateway_rest_api.main.id

  lifecycle {
    create_before_destroy = true
  }
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "apigw_root" {
  statement_id  = "AllowExecutionFromAPIGatewayRoot"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "apigw" {
  name              = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.main.id}/demo"
  retention_in_days = 14
}

# API Gateway Account (for CloudWatch logging)
resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch_role.arn
}

# API Gateway Stage
resource "aws_api_gateway_stage" "demo" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = "demo"

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.apigw.arn
    format = jsonencode({
      requestId               = "$context.requestId"
      ip                      = "$context.identity.sourceIp"
      caller                  = "$context.identity.caller"
      user                    = "$context.identity.user"
      requestTime             = "$context.requestTime"
      httpMethod              = "$context.httpMethod"
      resourcePath            = "$context.resourcePath"
      status                  = "$context.status"
      protocol                = "$context.protocol"
      responseLength          = "$context.responseLength"
      error                   = "$context.error.message"
      errorType               = "$context.error.messageString"
      integrationErrorMessage = "$context.integrationErrorMessage"
      responseTime            = "$context.responseTime"
    })
  }

  depends_on = [aws_api_gateway_account.main]
}

# Demo Lambda execution role (in test account)
resource "aws_iam_role" "demo_lambda_execution_role" {
  name = "noop-demo-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic execution role policy to the Lambda role
resource "aws_iam_role_policy_attachment" "demo_lambda_basic_execution" {
  role       = aws_iam_role.demo_lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# API Gateway CloudWatch role
resource "aws_iam_role" "api_gateway_cloudwatch_role" {
  name = "noop-apigw-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch_logs" {
  role       = aws_iam_role.api_gateway_cloudwatch_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}
