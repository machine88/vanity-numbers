########################################################
# Static web app (S3 + CloudFront with OAC, HTTPS)     #
########################################################

# Only create when enabled
locals {
  web_enabled  = var.enable_bonus_webapp
  apigw_domain = replace(aws_apigatewayv2_api.http.api_endpoint, "https://", "")
}

# Reuse AWS managed policies (no need to create custom ones)
data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

# Strip the Host header so API Gateway sees its own hostname, avoiding 403s
data "aws_cloudfront_origin_request_policy" "all_viewer_except_host" {
  name = "Managed-AllViewerExceptHostHeader"
}

# S3 bucket to hold site assets (private)
resource "aws_s3_bucket" "web" {
  count  = local.web_enabled ? 1 : 0
  bucket = "${var.project_name}-web-${local.account_id}"
  tags   = local.common_tags
}

# Block all public access (we'll allow CloudFront via OAC only)
resource "aws_s3_bucket_public_access_block" "web" {
  count                   = local.web_enabled ? 1 : 0
  bucket                  = aws_s3_bucket.web[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudFront Origin Access Control (OAC) for S3
resource "aws_cloudfront_origin_access_control" "oac" {
  count                             = local.web_enabled ? 1 : 0
  name                              = "${var.project_name}-oac"
  description                       = "OAC for ${var.project_name} static site"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# ---------------- CloudFront Distribution (global HTTPS) ----------------
resource "aws_cloudfront_distribution" "web" {
  count               = local.web_enabled ? 1 : 0
  enabled             = true
  comment             = "${var.project_name} static site"
  default_root_object = "index.html"

  # S3 origin for the website
  origin {
    domain_name              = aws_s3_bucket.web[0].bucket_regional_domain_name
    origin_id                = "s3-${aws_s3_bucket.web[0].id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac[0].id
  }

  # API Gateway origin for /last5*
  origin {
    origin_id   = "api-origin"
    domain_name = local.apigw_domain

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Default behavior -> S3 site
  default_cache_behavior {
    target_origin_id       = "s3-${aws_s3_bucket.web[0].id}"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]
    compress        = true

    # simple inline cache settings (you can swap to a managed policy if you like)
    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }
  }

  # Route /last5* -> API origin; disable edge caching; strip Host header
  ordered_cache_behavior {
    path_pattern           = "/last5*"
    target_origin_id       = "api-origin"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]
    compress        = true

    cache_policy_id          = data.aws_cloudfront_cache_policy.caching_disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host.id
  }

  # Open to all countries; restrict if needed
  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  # Use CloudFront default cert for *.cloudfront.net
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = local.common_tags
}
# ---------------- End CloudFront Distribution ----------------

# Bucket policy: allow CloudFront OAC to read objects
data "aws_iam_policy_document" "web_bucket_policy" {
  count = local.web_enabled ? 1 : 0

  statement {
    sid       = "AllowCloudFrontOAC"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.web[0].arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.web[0].arn]
    }
  }
}

resource "aws_s3_bucket_policy" "web" {
  count  = local.web_enabled ? 1 : 0
  bucket = aws_s3_bucket.web[0].id
  policy = data.aws_iam_policy_document.web_bucket_policy[0].json

  depends_on = [aws_s3_bucket_public_access_block.web]
}

#############################################
# Upload built site assets to the S3 bucket #
#############################################

resource "aws_s3_object" "index" {
  count        = local.web_enabled ? 1 : 0
  bucket       = aws_s3_bucket.web[0].id
  key          = "index.html"
  source       = "${path.module}/../build/site/index.html"
  etag         = filemd5("${path.module}/../build/site/index.html")
  content_type = "text/html"
}

resource "aws_s3_object" "app" {
  count        = local.web_enabled ? 1 : 0
  bucket       = aws_s3_bucket.web[0].id
  key          = "app.js"
  source       = "${path.module}/../build/site/app.js"
  etag         = filemd5("${path.module}/../build/site/app.js")
  content_type = "application/javascript"
}