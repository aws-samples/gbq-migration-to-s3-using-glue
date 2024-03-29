variable "name_prefix" {
  type = string
  description = "Name Prefix of the Resource"
  default = "sample"
}

variable "env" {
  type = string
  description = "Deployment Environment"
  default = "dev"
}

variable "type" {
  type = string
  description = "Type of Data i.e. incremental or historical"
  default = "incremental"
}

variable "sources" {
  type = string
  description = "Source of Data i.e gbq"
  default = "gbq"
}

variable "s3_prefix_source" {
  type = string
  description = "Prefix used for the landing bucket"
  default = "gbq"
}


variable "assets_bucket" {
    type = string
    description = "The S3 Asset Bucket where the Glue Scripts will be stored"
}

variable s3_landing_bucket {
    type = string
    description = "The S3 Landing Bucket"
}

variable glue_version {
    type = string
    default = "3.0"
}

variable glue_job_timeout {
    type = string
    default = "2880"
}

variable "glue_worker_type" {
  type = string
  default = "G.1X"
}

variable "glue_number_of_workers" {
  type = string
  default = "10"
}

variable "connector_class" {
  type = string
  description = "GBQ Glue Connector Class"
  default = "com.google.cloud.spark.bigquery"
}

variable "connector_url" {
  type = string
  description = "GBQ Glue Connector URL"
  default = "https://709825985650.dkr.ecr.us-east-1.amazonaws.com/amazon-web-services/glue/bigquery:0.24.2-glue3.0"
}

