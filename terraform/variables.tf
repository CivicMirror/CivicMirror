# ── GCP ──────────────────────────────────────────────────────────────────────
variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "civicmirror-2026"
}

variable "gcp_region" {
  description = "GCP region for Cloud Run services"
  type        = string
  default     = "us-central1"
}

variable "github_repo" {
  description = "GitHub repository in owner/repo format (scopes WIF trust)"
  type        = string
  default     = "tokendad/CivicMirror"
}

# ── Cloud Run — Backend ───────────────────────────────────────────────────────
variable "backend_cpu" {
  type    = string
  default = "1"
}

variable "backend_memory" {
  type    = string
  default = "512Mi"
}

variable "backend_min_instances" {
  type    = number
  default = 0
}

variable "backend_max_instances" {
  type    = number
  default = 3
}

variable "gunicorn_workers" {
  type    = number
  default = 2
}

# ── Cloud Run — Frontend ──────────────────────────────────────────────────────
variable "frontend_min_instances" {
  type    = number
  default = 0
}

variable "frontend_max_instances" {
  type    = number
  default = 3
}

# ── Cloudflare ────────────────────────────────────────────────────────────────
variable "cloudflare_api_token" {
  description = "Cloudflare API token with Zone:DNS:Edit permission"
  type        = string
  sensitive   = true
  default     = ""
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID for welshrd.com"
  type        = string
  default     = ""
}
