variable "region" {
  default = "us-east-1"
}

variable "bucket_name" {
  description = "Nombre del bucket S3"
  type        = string
  default     = "artefact-data-pipeline-bucket"
}

variable "lambda_function_name" {
  description = "Nombre de la función Lambda"
  default     = "IngestGalacticPeople"
}
