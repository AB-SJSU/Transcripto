data "aws_iam_policy_document" "assume_ec2" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "assume_lambda" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_instance_profile" "worker_profile" {
  name = "TranscriptoWorkerTaskRole"
  role = aws_iam_role.worker.name
}

resource "aws_iam_instance_profile" "api_profile" {
  name = "TranscriptoApiEC2Role"
  role = aws_iam_role.api.name
}

resource "aws_iam_role" "worker" {
  name               = "TranscriptoWorkerTaskRole"
  description        = "Allows EC2 instances to call AWS services on your behalf."
  assume_role_policy = data.aws_iam_policy_document.assume_ec2.json
}

resource "aws_iam_role" "api" {
  name               = "TranscriptoApiEC2Role"
  description        = "Allows EC2 instances to call AWS services on your behalf."
  assume_role_policy = data.aws_iam_policy_document.assume_ec2.json
}

resource "aws_iam_role" "notify" {
  name               = "TranscriptoNotifyLambdaRole"
  description        = "Allows Lambda functions to call AWS services on your behalf."
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
}