locals {
  backend_secret_env_vars = [
    { name = "DJANGO_SECRET_KEY", secret_id = "DJANGO_SECRET_KEY" },
    { name = "DATABASE_URL", secret_id = "DATABASE_URL" },
    { name = "REDIS_URL", secret_id = "REDIS_URL" },
    { name = "CIVIC_API_KEY", secret_id = "CIVIC_API_KEY" },
  ]
}

# ── Backend (Django + Gunicorn) ───────────────────────────────────────────────
resource "google_cloud_run_v2_service" "backend" {
  name                = "civicmirror-backend"
  location            = var.gcp_region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = data.google_service_account.cloud_run_runtime.email

    vpc_access {
      connector = data.google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    scaling {
      min_instance_count = var.backend_min_instances
      max_instance_count = var.backend_max_instances
    }

    containers {
      image = "us-central1-docker.pkg.dev/${var.gcp_project_id}/civicmirror-images/backend:latest"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = var.backend_cpu
          memory = var.backend_memory
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      env {
        name  = "DJANGO_SETTINGS_MODULE"
        value = "config.settings.prod"
      }
      env {
        name  = "DJANGO_ALLOWED_HOSTS"
        value = "api.civicmirror.welshrd.com,.run.app,localhost"
      }
      env {
        name  = "FRONTEND_BASE_URL"
        value = "https://civicmirror.welshrd.com"
      }
      env {
        name  = "CORS_ALLOWED_ORIGINS"
        value = "https://civicmirror.welshrd.com"
      }
      env {
        name  = "GUNICORN_WORKERS"
        value = tostring(var.gunicorn_workers)
      }

      dynamic "env" {
        for_each = local.backend_secret_env_vars
        content {
          name = env.value.name
          value_source {
            secret_key_ref {
              secret  = env.value.secret_id
              version = "latest"
            }
          }
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [data.google_sql_database_instance.db.connection_name]
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].containers[0].image]
  }
}

resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  project  = var.gcp_project_id
  location = var.gcp_region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Frontend (nginx + React) ──────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "frontend" {
  name                = "civicmirror-frontend"
  location            = var.gcp_region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    scaling {
      min_instance_count = var.frontend_min_instances
      max_instance_count = var.frontend_max_instances
    }

    containers {
      image = "us-central1-docker.pkg.dev/${var.gcp_project_id}/civicmirror-images/frontend:latest"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "256Mi"
        }
        cpu_idle = true
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].containers[0].image]
  }
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  project  = var.gcp_project_id
  location = var.gcp_region
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Domain Mappings ───────────────────────────────────────────────────────────
# Note: Cloud Run domain mappings use the v1 API resource even for v2 services.
# After first `terraform apply`, the domain mapping returns DNS records to add
# (for subdomains: CNAME → ghs.googlehosted.com).
# Set cloudflare_record.proxied = false during initial cert provisioning, then
# switch to true once Google has issued the managed certificate.

resource "google_cloud_run_domain_mapping" "backend" {
  location = var.gcp_region
  name     = "api.civicmirror.welshrd.com"
  project  = var.gcp_project_id

  metadata {
    namespace = var.gcp_project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.backend.name
  }
}

resource "google_cloud_run_domain_mapping" "frontend" {
  location = var.gcp_region
  name     = "civicmirror.welshrd.com"
  project  = var.gcp_project_id

  metadata {
    namespace = var.gcp_project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.frontend.name
  }
}

# ── Sync Elections — Cloud Run Job ────────────────────────────────────────────
resource "google_cloud_run_v2_job" "sync_elections" {
  name                = "civicmirror-sync-elections"
  location            = var.gcp_region
  project             = var.gcp_project_id
  deletion_protection = false

  template {
    task_count  = 1
    parallelism = 1

    template {
      service_account = data.google_service_account.cloud_run_runtime.email
      max_retries     = 0
      timeout         = "3600s"

      vpc_access {
        connector = data.google_vpc_access_connector.connector.id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image   = "us-central1-docker.pkg.dev/${var.gcp_project_id}/civicmirror-images/backend:latest"
        command = ["python"]
        args    = ["manage.py", "sync_civic_elections"]

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }

        env {
          name  = "DJANGO_SETTINGS_MODULE"
          value = "config.settings.prod"
        }
        env {
          name  = "DJANGO_ALLOWED_HOSTS"
          value = "localhost"
        }
        # Run all Celery tasks in-process (no worker needed in this job).
        env {
          name  = "CELERY_TASK_ALWAYS_EAGER"
          value = "true"
        }
        # Do not propagate per-address exceptions so one failure doesn't abort the whole job.
        env {
          name  = "CELERY_TASK_EAGER_PROPAGATES"
          value = "false"
        }

        dynamic "env" {
          for_each = local.backend_secret_env_vars
          content {
            name = env.value.name
            value_source {
              secret_key_ref {
                secret  = env.value.secret_id
                version = "latest"
              }
            }
          }
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [data.google_sql_database_instance.db.connection_name]
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].template[0].containers[0].image]
  }
}
