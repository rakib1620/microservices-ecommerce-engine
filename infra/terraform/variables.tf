variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS Region for provisioning infrastructure"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR block for the custom VPC"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Deployment environment name"
}
