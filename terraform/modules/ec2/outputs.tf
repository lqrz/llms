output "instance_id" {
  description = "ID of the webserver instance."
  value       = aws_instance.webserver.id
}
