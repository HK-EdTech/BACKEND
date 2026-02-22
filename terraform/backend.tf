terraform {
  backend "s3" {
    # Fill these in after running terraform/bootstrap.
    # These are not sensitive — bucket/table names are safe to commit.
    bucket         = "hk-edtech-tfstate"
    key            = "dev/terraform.tfstate"
    region         = "ap-southeast-2"
    dynamodb_table = "hk-edtech-tflock"
    encrypt        = true
  }
}
