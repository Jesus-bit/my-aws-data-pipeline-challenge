output "s3_bucket_name" {
  value = aws_s3_bucket.data_pipeline.id
}

output "lambda_function_name" {
  value = aws_lambda_function.ingest_people.function_name
}

output "lambda_invoke_command" {
  value = "aws lambda invoke --function-name ${aws_lambda_function.ingest_people.function_name} response.json"
}
