output "lambda_function_arn" {
  value       = aws_lambda_function.main.arn
  description = "ARN of the demo Lambda function"
}

output "api_gateway_url" {
  value       = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${data.aws_region.current.region}.amazonaws.com/demo"
  description = "URL of the demo API Gateway"
}
