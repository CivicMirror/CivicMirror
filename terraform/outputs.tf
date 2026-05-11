output "backend_cloud_run_url" {
  description = "Backend Cloud Run service URL (internal .run.app URL)"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_cloud_run_url" {
  description = "Frontend Cloud Run service URL (internal .run.app URL)"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "app_url" {
  description = "Public frontend URL (via Cloudflare)"
  value       = "https://civicmirror.welshrd.com"
}

output "api_url" {
  description = "Public API URL (via Cloudflare)"
  value       = "https://api.civicmirror.welshrd.com"
}

output "wif_provider" {
  description = "Workload Identity Federation provider — set as GCP_WIF_PROVIDER GitHub secret"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "github_deployer_email" {
  description = "GitHub Actions deploy service account email — set as GCP_SERVICE_ACCOUNT GitHub secret"
  value       = data.google_service_account.github_deployer.email
}

output "artifact_registry_url" {
  description = "Artifact Registry base URL for image tags"
  value       = "us-central1-docker.pkg.dev/${var.gcp_project_id}/civicmirror-images"
}
