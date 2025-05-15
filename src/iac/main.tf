provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "data_pipeline" {
  bucket = var.bucket_name

  tags = {
    Environment = "Dev"
    Owner       = "Baz"
  }
}

# Opcionalmente, puedes crear carpetas iniciales (raw y processed)
resource "aws_s3_object" "folders" {
  for_each = toset(["raw/", "processed/"])
  bucket   = aws_s3_bucket.data_pipeline.id
  key      = each.key
  content  = ""
}

# Rol de ejecución para la Lambda
resource "aws_iam_role" "lambda_exec" {
  name = "${var.lambda_function_name}_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Permisos para la Lambda (escribir en S3 + logs)
resource "aws_iam_policy_attachment" "lambda_policy" {
  name       = "lambda-s3-attach"
  roles      = [aws_iam_role.lambda_exec.name]
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_policy_attachment" "logs_policy" {
  name       = "lambda-logs-attach"
  roles      = [aws_iam_role.lambda_exec.name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Crear un archivo ZIP de la Lambda local
data "archive_file" "lambda_package" {
  type        = "zip"
  source_file = "${path.module}/lambda/ingest_people.py"
  output_path = "${path.module}/lambda/ingest_people.zip"
}

# Crear la función Lambda
resource "aws_lambda_function" "ingest_people" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = var.lambda_function_name
  role             = aws_iam_role.lambda_exec.arn
  handler          = "ingest_people.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256(data.archive_file.lambda_package.output_path)

  environment {
    variables = {
      BUCKET_NAME = var.bucket_name
    }
  }

  depends_on = [
    aws_iam_role.lambda_exec
  ]
}
