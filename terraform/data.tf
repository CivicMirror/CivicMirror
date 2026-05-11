data "google_service_account" "cloud_run_runtime" {
  account_id = "cloudrun-runtime"
  project    = var.gcp_project_id
}

data "google_service_account" "github_deployer" {
  account_id = "github-deployer"
  project    = var.gcp_project_id
}

data "google_sql_database_instance" "db" {
  name    = "civicmirror-db"
  project = var.gcp_project_id
}

data "google_vpc_access_connector" "connector" {
  name    = "civicmirror-connector"
  region  = var.gcp_region
  project = var.gcp_project_id
}

data "google_artifact_registry_repository" "images" {
  repository_id = "civicmirror-images"
  location      = var.gcp_region
  project       = var.gcp_project_id
}
