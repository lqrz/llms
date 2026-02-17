aws_region            = "us-east-2"
project           = "financial-consultant"
name_prefix           = "financial-consultant"
vpc_cidr              = "10.0.0.0/16"
availability_zone_configs = {
    "us-east-2a": { public_cidr = "10.0.1.0/24", private_cidr = "10.0.2.0/24" }
    "us-east-2b": { public_cidr = "10.0.3.0/24", private_cidr = "10.0.4.0/24" }
}
enable_dns_support    = true
enable_dns_hostnames  = true
# ami_id = "ami-03ea746da1a2e36e7"
# instance_type = "t3.micro"
# instance_volume_size = 8
frontend_container_image_uri = ""
frontend_health_path = "/health"
frontend_port = 8001
ecs_frontend_desired_count = 1
frontend_envvars = {
    API_TIMEOUT = "300"
}
backend_container_image_uri = ""
backend_health_path = "/health"
backend_port = 8000
ecs_backend_desired_count = 1
backend_envvars = {
    LOG_LEVEL               = "INFO"
    DEFAULT_LLM_PROVIDER     = "OPENAI"
    DEFAULT_LLM_MODEL        = "gpt-4.1-nano"
    DEFAULT_EMBEDDING_PROVIDER = "openai"
    DEFAULT_EMBEDDING_MODEL  = "text-embedding-3-small"
    WEAVIATE_URL             = "http://localhost:8080"
    HYBRID_SEARCH_ALPHA      = "0.5"
    RETRIEVAL_TOP_K          = "20"
    RERANK_TOP_N             = "5"
    RERANKER_TYPE            = "local"
    LOCAL_RERANKER_MODEL     = "cross-encoder/ms-marco-MiniLM-L-12-v2"
}
ecr_repository_names = ["frontend", "backend", "db", "vector-db"]
image_tag_mutability = "MUTABLE"
scan_on_push = true
ecs_task_cpu = 1024
ecs_task_memory = 2048
ecs_enable_container_insights = true
secret_keys = [ "OPENAI_API_KEY", "GEMINI_API_KEY", "COHERE_API_KEY", "WEAVIATE_API_KEY", "LANGSMITH_API_KEY" ]
tags                  = {}
