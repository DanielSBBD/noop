terraform {
  backend "s3" {
    bucket         = "noop-demo-sample-app"
    key            = "noop-demo/terraform.tfstate"
    region         = "us-east-1"
    profile        = "MServAI"
    dynamodb_table = "noop-demo-sample-app"
    encrypt        = true
  }
}
