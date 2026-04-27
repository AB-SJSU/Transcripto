resource "aws_dynamodb_table" "jobs" {
  name         = "TranscriptionJobs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "jobId"

  attribute {
    name = "jobId"
    type = "S"
  }
}