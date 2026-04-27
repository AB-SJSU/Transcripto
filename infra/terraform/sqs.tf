resource "aws_sqs_queue" "dlq" {
  name             = "transcripto-job-dlq"
  max_message_size = 1048576
}

resource "aws_sqs_queue" "job" {
  name                       = "transcripto-job-queue"
  max_message_size           = 1048576
  visibility_timeout_seconds = 600

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "notify" {
  name             = "transcripto-notify-queue"
  max_message_size = 1048576
}