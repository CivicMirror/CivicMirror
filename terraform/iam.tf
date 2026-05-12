# Artifact Registry Writer — push images from GitHub Actions
resource "google_project_iam_member" "github_ar_writer" {
  project = var.gcp_project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${data.google_service_account.github_deployer.email}"
}

# Cloud Run Developer — deploy new revisions
resource "google_project_iam_member" "github_run_developer" {
  project = var.gcp_project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${data.google_service_account.github_deployer.email}"
}

# Act as the Cloud Run runtime SA (required to deploy with a custom SA)
resource "google_service_account_iam_member" "github_act_as_run" {
  service_account_id = data.google_service_account.cloud_run_runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${data.google_service_account.github_deployer.email}"
}

resource "google_cloud_run_v2_job_iam_member" "scheduler_invoke_sync" {
  project  = var.gcp_project_id
  location = var.gcp_region
  name     = google_cloud_run_v2_job.sync_elections.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${data.google_service_account.cloud_run_runtime.email}"
}

# Grant cloudrun-runtime access to read secrets
locals {
  runtime_secrets = ["DJANGO_SECRET_KEY", "DATABASE_URL", "REDIS_URL", "CIVIC_API_KEY"]
}

resource "google_secret_manager_secret_iam_member" "runtime_secret_access" {
  for_each  = toset(local.runtime_secrets)
  project   = var.gcp_project_id
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_service_account.cloud_run_runtime.email}"
}
