output "audio_bucket" { value = aws_s3_bucket.audio.bucket }
output "transcript_bucket" { value = aws_s3_bucket.transcript.bucket }

output "job_queue_url" { value = aws_sqs_queue.job.url }
output "dlq_url" { value = aws_sqs_queue.dlq.url }
output "notify_queue_url" { value = aws_sqs_queue.notify.url }

output "ddb_table" { value = aws_dynamodb_table.jobs.name }

output "launch_template_name" { value = aws_launch_template.worker_lt.name }
output "asg_name" { value = aws_autoscaling_group.worker_asg.name }