data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

locals {
 arn_prefix = "arn:aws:kms:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:key"
}

resource "aws_iam_role" "glue" {
  name = "${local.name}-glue-service-role-${var.env}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "glue.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "s3_access" {
  role       = "${aws_iam_role.glue.name}"
  policy_arn = aws_iam_policy.s3_bucket.arn
}

resource "aws_iam_role_policy_attachment" "glue_access" {
  role       = "${aws_iam_role.glue.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy_attachment" "read_secrets_manager" {
  role       = "${aws_iam_role.glue.name}"
  policy_arn = aws_iam_policy.read_secrets_manager.arn
}

resource "aws_iam_role_policy_attachment" "kms" {
  role       = "${aws_iam_role.glue.name}"
  policy_arn = aws_iam_policy.kms.arn
}

resource "aws_iam_role_policy_attachment" "ecr" {
  role       = "${aws_iam_role.glue.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_secretsmanager_secret" "secrets" {
  name = "${local.name}-base64-glue-secrets-store-${var.env}"
}

resource "aws_secretsmanager_secret" "secrets_json" {
  name = "${local.name}-json-glue-secrets-store-${var.env}"
}


resource "aws_iam_policy" "read_secrets_manager" {
  name        = "${local.name}-read-secrets-${var.env}"
  description = "Access for Glue to Read Secrets Manager"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "secretsmanager:GetResourcePolicy",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds"
      ],
      "Effect": "Allow",
      "Resource": ["${aws_secretsmanager_secret.secrets.arn}",
      "${aws_secretsmanager_secret.secrets_json.arn}"]
    },
    {
        "Effect": "Allow",
        "Action": "secretsmanager:ListSecrets",
        "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_iam_policy" "kms" {
  name        = "${local.name}-kms-decrypt-${var.env}"
  description = "Access for Glue for KMS Decryption"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
            "kms:GetParametersForImport",
            "kms:GetPublicKey",
            "kms:Decrypt",
            "kms:Encrypt",
            "kms:GetKeyRotationStatus",
            "kms:GetKeyPolicy",
            "kms:GenerateDataKey",
            "kms:DescribeKey"
      ],
      "Effect": "Allow",
      "Resource": ["${local.arn_prefix}/${var.assets_bucket_kms_key}",
      "${local.arn_prefix}/${var.landing_bucket_kms_key}"]
    },
    {
        "Effect": "Allow",
        "Action": "kms:DescribeCustomKeyStores",
        "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_iam_policy" "s3_bucket" {
  name        = "${local.name}-s3-${var.env}"
  description = "Access for S3 Bucket"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "s3:PutObject"
      ],
      "Effect": "Allow",
      "Resource": ["arn:aws:s3:::${var.s3_landing_bucket}/*"]
    },
    {
        "Effect": "Allow",
        "Action": ["s3:GetObject"],
        "Resource": ["arn:aws:s3:::${var.assets_bucket}/*"]
    }
  ]
}
EOF
}

resource "aws_glue_job" "gbq_instance_job" {
  for_each = {for database in var.table_map: database.index => database}
  name     = "${local.name}-glue-job-${each.value.index}-${var.env}"
  role_arn = aws_iam_role.glue.arn
  description = "Glue Job to transfer incremental Data from SQL Database to S3"
  command {
    script_location = "s3://${var.assets_bucket}/glue/gbq_incremental.py"
  }
  glue_version = var.glue_version
  number_of_workers         = var.glue_number_of_workers
  worker_type               = var.glue_worker_type
  timeout        = var.glue_job_timeout
  default_arguments = {
    "--job-bookmark-option": "job-bookmark-enable",
    "--region_name" = data.aws_region.current.name,
    "--s3_path" = "s3://${var.s3_landing_bucket}/input/${var.s3_prefix_source}",
    "--parent_project" = each.value.parent_project
    "--dataset" = each.value.dataset
    "--secret_name" = aws_secretsmanager_secret.secrets_json.name
    "--additional-python-modules" = "google-cloud-bigquery==3.3.5"
    "--s3_bucket" = var.assets_bucket
    "--tables_file" = each.value.tables_file
    "--extra-py-files": "s3://${var.assets_bucket}/glue/gbq_incremental_lib.py"
  }
  connections = [aws_glue_connection.gbq_instance.name]
}

resource "aws_glue_connection" "gbq_instance" {
  name = "${local.name}-glue-connection-${var.env}"
  connection_type = "MARKETPLACE"
  connection_properties = {
      CONNECTOR_CLASS_NAME = var.connector_class
      CONNECTOR_URL = var.connector_url
      SECRET_ID = aws_secretsmanager_secret.secrets.id
      CONNECTOR_TYPE = "Spark"
    }
}



