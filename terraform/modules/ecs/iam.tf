# # hardcoding this existing IAM role
# # since i do not have permissions to create one.
# data "aws_iam_role" "this" {
#   name = "ecsTaskExecutionRole"
# }

# create trust policy
data "aws_iam_policy_document" "ecs_task_execution_assume_role" {
  statement {
    effect = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# create role (w/ trust policy)
resource "aws_iam_role" "this" {
  name               = "${var.name_prefix}-ecs-task-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume_role.json

  tags = merge(
    {
        Name = "${var.name_prefix}-ecs-task-execution-role"
    },
    var.tags
  )
}

# attach managed policy to role
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role" {
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# get policy w/ get secret permissions
data "aws_iam_policy_document" "execution_secrets_read" {
  statement {
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [ var.secrets_manager_arn]
  }
}

# attach json inline policy in role
resource "aws_iam_role_policy" "execution_secrets_read_inline" {
  name   = "${var.name_prefix}-execution-secrets-read"
  role   = aws_iam_role.this.id
  policy = data.aws_iam_policy_document.execution_secrets_read.json
}
