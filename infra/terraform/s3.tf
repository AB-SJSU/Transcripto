resource "aws_s3_bucket" "audio" {
  bucket = "transcripto-audio-bucket"
}

resource "aws_s3_bucket" "transcript" {
  bucket = "transcripto-transcript-bucket"
}

resource "aws_s3_bucket_public_access_block" "audio" {
  bucket                  = aws_s3_bucket.audio.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "transcript" {
  bucket                  = aws_s3_bucket.transcript.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "audio" {
  bucket = aws_s3_bucket.audio.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "transcript" {
  bucket = aws_s3_bucket.transcript.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Audio lifecycle: expire after 30 days
resource "aws_s3_bucket_lifecycle_configuration" "audio" {
  bucket = aws_s3_bucket.audio.id

  rule {
    id     = "expire-audio-after-30-days"
    status = "Enabled"
    filter {}

    expiration {
      days = 30
    }
  }

  # AWS/Terraform represent empty filters slightly differently → plan noise
  lifecycle {
    ignore_changes = [rule]
  }
}

# Transcript lifecycle: transition to STANDARD_IA at 30 days, expire at 60 days
resource "aws_s3_bucket_lifecycle_configuration" "transcript" {
  bucket = aws_s3_bucket.transcript.id

  rule {
    id     = "expire-transcripts-after-30-days"
    status = "Enabled"
    filter {}

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    expiration {
      days = 60
    }
  }

  # Same normalization issue as above
  lifecycle {
    ignore_changes = [rule]
  }
}