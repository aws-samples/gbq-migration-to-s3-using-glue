# Google Big Query Terraform Files
This folder specifies the Terraform IAC for Google Big Query (GBQ)

## .tf Files Description
| File Name | Description |
|-----|-----|
| init.tf | Initializes the Terraform State and specifies the Bucket and Folder where the GBQ state is stored |
| main.tf | This is the file that contains the IAC for the Glue Resource, Connections and the IAM Role/Permissions needed
| variables.tf | This is the file that contains the variables required to deploy GBQ|
| locals.tf | File to store the local variable |
| tablemap.tf | Map consisting the JSON Files to the S3 Bucket |

main.tf will deploy two secrets manager instance
1. `sample-gbq-incremental-base64-glue-secrets-store-<env>` has the json credentials stored in base64 format.  This will be used by the GBQ Connector to authenticate with the service account

2. `sample-gbq-incremental-json-glue-secrets-store-<env>` has the Service Account JSON Credentials.  This will used by the GBQ Client in the Glue Job to authorize with the service account

### tablemap.tf

Here you can specify a map containing a list of objects.

| Object Parameters | Value |
|----|----|
| index | Number of Object in the list, e.g. if it's the first object in the list, the value would be 1 |  
| dataset | `dataset name` | 
| parent_project | `<<google_project_id>>` |
| tables_file | S3 Path to the JSON File containing the Objects | 

### variables.tf
 
This is the file that would contain the declaration and the type of the variables needed

For e.g:
```
variable "env" {
  type = string
  description = "Deployment Environment"
}
```
Here `env` is the name of the variable and the type is string

If you want to inject the value defined in variables.tf by the pipeline, export it like this:
`export TF_VAR_env = dev`

If you want to specify it in the variable file, you can create a terraform.tfvars file 

For e.g. create a file `terraform.tfvars` and specify the variables
```
env = "dev"
vpc_id = <VPC ID>
s3_landing_bucket = <Name of the S3 Landing Bucket>
assets_bucket = <Name of the S3 Assets Bucket>
```
Note: This is an example and more variables can be added accordingly
