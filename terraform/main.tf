locals {
  azs_sorted = sort(keys(module.network.availability_zones))
  public_subnet_ids = [
    for az in local.azs_sorted : module.network.availability_zones[az].public_subnet_id
  ]
  private_subnet_ids = [
    for az in local.azs_sorted: module.network.availability_zones[az].private_subnet_id
  ]

  base_tags = merge(
    {
      project = var.name_prefix
    },
    var.tags
  )
}

module "network" {
  source = "./modules/network"

  name_prefix           = var.name_prefix
  project = var.project
  vpc_cidr              = var.vpc_cidr
  enable_dns_support    = var.enable_dns_support
  enable_dns_hostnames  = var.enable_dns_hostnames
  availability_zone_configs = var.availability_zone_configs
  tags                  = local.base_tags
}

module "ecs" {
  source = "./modules/ecs"

  aws_region = var.aws_region
  name_prefix = var.name_prefix
  vpc_id = module.network.vpc_id
  subnet_ids = local.private_subnet_ids
  enable_container_insights=var.ecs_enable_container_insights
  task_cpu = var.ecs_task_cpu
  task_memory = var.ecs_task_memory
  # --- frontend service
  frontend_port = var.frontend_port
  frontend_container_image_uri = var.frontend_container_image_uri
  frontend_desired_count = var.ecs_frontend_desired_count
  frontend_alb_target_group_arn = module.alb.frontend_target_group_arn
  frontend_security_group_id = module.alb.frontend_security_group_id
  frontend_envvars = var.frontend_envvars
  # --- backend service
  backend_port = var.backend_port
  backend_container_image_uri = var.backend_container_image_uri
  backend_desired_count = var.ecs_backend_desired_count
  backend_alb_target_group_arn = module.alb.backend_target_group_arn
  backend_security_group_id = module.alb.backend_security_group_id
  backend_url = module.alb.backend_dns
  backend_envvars = var.backend_envvars
  # --- others
  tags        = local.base_tags
  secrets_manager_arn = module.secrets.secrets_manager_arn
  secret_keys = var.secret_keys
}

module "alb" {
  source = "./modules/alb"
   
  name_prefix         = var.name_prefix
  vpc_id              = module.network.vpc_id
  public_subnet_ids      = local.public_subnet_ids
  private_subnet_ids = local.private_subnet_ids
  frontend_task_security_group_id = module.ecs.frontend_task_security_group_id
  frontend_health_path = var.frontend_health_path
  frontend_port = var.frontend_port
  backend_health_path = var.backend_health_path
  backend_port = var.backend_port
  tags          = local.base_tags
}

module "ecr" {
  source = "./modules/ecr"
  for_each = toset(var.ecr_repository_names)

  name_prefix = var.name_prefix
  repository_name = each.value
  image_tag_mutability = var.image_tag_mutability
  scan_on_push = var.scan_on_push
  tags          = local.base_tags
}

module "secrets" {
  source = "./modules/secrets"

  name_prefix = var.name_prefix
  tags = local.base_tags
}
