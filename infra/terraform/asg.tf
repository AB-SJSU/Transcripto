resource "aws_launch_template" "worker_lt" {
  name          = "transcripto-worker-lt"
  description   = "transcripto-worker-with DLQ logic modified"
  image_id      = "ami-0818a7d085d24b23d"
  instance_type = "t3.small"
  key_name      = "cmpe281"

  vpc_security_group_ids = ["sg-0f0a49bdb018352cb"]

  iam_instance_profile {
    arn = "arn:aws:iam::164995165456:instance-profile/TranscriptoWorkerTaskRole"
  }

  # AWS sometimes stores/returns this differently; keep and ignore drift
  private_dns_name_options {
    hostname_type                        = "ip-name"
    enable_resource_name_dns_a_record    = false
    enable_resource_name_dns_aaaa_record = false
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name    = "transcripto-worker-asg"
      Project = "Transcripto"
    }
  }

  lifecycle {
    ignore_changes = [
      private_dns_name_options
    ]
  }
}

# Read the existing ASG so we can reuse its exact subnet list
data "aws_autoscaling_group" "existing_worker_asg" {
  name = "transcripto-worker-asg"
}

resource "aws_autoscaling_group" "worker_asg" {
  name                             = "transcripto-worker-asg"
  min_size                         = 1
  max_size                         = 3
  desired_capacity                 = 1
  force_delete                     = false
  force_delete_warm_pool           = false
  ignore_failed_scaling_activities = false

  # Use the exact current subnet list from AWS to prevent "subnet diff"
  vpc_zone_identifier = split(",", data.aws_autoscaling_group.existing_worker_asg.vpc_zone_identifier)

  launch_template {
    id      = aws_launch_template.worker_lt.id
    version = "$Default"
  }

  instance_maintenance_policy {
    min_healthy_percentage = 90
    max_healthy_percentage = 100
  }

  tag {
    key                 = "Name"
    value               = "transcripto-worker-asg"
    propagate_at_launch = true
  }

  tag {
    key                 = "Project"
    value               = "Transcripto"
    propagate_at_launch = true
  }

  # These provider-computed defaults create noise; ignore them
  lifecycle {
    ignore_changes = [
      wait_for_capacity_timeout,
      force_delete,
      force_delete_warm_pool,
      ignore_failed_scaling_activities
    ]
  }
}