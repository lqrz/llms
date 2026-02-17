locals {
  base_tags = merge(
    {
      project = var.name_prefix
    },
    var.tags
  )
  name = "${var.name_prefix}-webserver"
}

# --------------
# TODO: delete this iam role. 
# cannot do it now cause of permissions issues.
data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    effect = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ec2_ssm_role" {
  name               = "${local.name}-iam-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = merge({
      Name = "${local.name}-iam-role"
    },
    local.base_tags
  )
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ec2_ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2_ssm_profile" {
  name = "${local.name}-ec2-ssm-profile"
  role = aws_iam_role.ec2_ssm_role.name

  tags = merge({
      Name = "${local.name}-ec2-ssm-profile"
    },
    local.base_tags
  )
}
# --------------

resource "aws_instance" "webserver" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [var.security_group_id]
  associate_public_ip_address = false
  iam_instance_profile = aws_iam_instance_profile.ec2_ssm_profile.name

  tags = merge(
    {
      Name = "${local.name}"
    },
    local.base_tags
  )

  # Tags applied to the EBS volumes created with this instance (root + ebs_block_device)
  volume_tags = merge(
      {
        Name = "${local.name}-volume"
      },
      local.base_tags
    )
 
}
