# Subdomains use CNAME records pointing to GCP's Cloud Run gateway.
# GCP Cloud Run domain mappings for subdomains target ghs.googlehosted.com.
#
# IMPORTANT: Set proxied = false on first apply to allow Google to provision
# its managed SSL certificate via DNS validation. Once the cert shows "Active"
# in GCP Console (Cloud Run → Domain Mappings), change to proxied = true and
# re-apply. With Cloudflare in Full SSL mode, the origin (GCP) uses its cert
# and Cloudflare issues its own cert to the client.

resource "cloudflare_record" "backend_api" {
  zone_id = var.cloudflare_zone_id
  name    = "api.civicmirror"
  content = "ghs.googlehosted.com"
  type    = "CNAME"
  proxied = false  # switch to true after GCP managed cert shows Active
  ttl     = 1
  comment = "CivicMirror API → Cloud Run backend — managed by Terraform"
}

resource "cloudflare_record" "frontend_app" {
  zone_id = var.cloudflare_zone_id
  name    = "civicmirror"
  content = "ghs.googlehosted.com"
  type    = "CNAME"
  proxied = false  # switch to true after GCP managed cert shows Active
  ttl     = 1
  comment = "CivicMirror App → Cloud Run frontend — managed by Terraform"
}
