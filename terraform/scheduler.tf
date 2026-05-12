# ── Cloud Scheduler — hourly election sync ────────────────────────────────────
# Triggers the civicmirror-sync-elections Cloud Run Job every hour on the hour.
# Uses the cloud_run_runtime service account (granted roles/run.invoker on the
# job in iam.tf) so no separate scheduler SA is needed.
resource "google_cloud_scheduler_job" "sync_elections_hourly" {
  name     = "sync-elections-hourly"
  schedule = "0 * * * *"
  region   = var.gcp_region
  project  = var.gcp_project_id

  http_target {
    http_method = "POST"
    uri = join("", [
      "https://run.googleapis.com/v2/projects/",
      var.gcp_project_id,
      "/locations/",
      var.gcp_region,
      "/jobs/",
      google_cloud_run_v2_job.sync_elections.name,
      ":run",
    ])

    oauth_token {
      service_account_email = data.google_service_account.cloud_run_runtime.email
    }
  }

  depends_on = [google_cloud_run_v2_job_iam_member.scheduler_invoke_sync]
}
