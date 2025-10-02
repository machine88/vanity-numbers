########################################################
# Static web app (S3 + CloudFront with OAC, HTTPS)     #
########################################################

# Only create when enabled
locals {
  web_enabled = var.enable_bonus_webapp
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

# CloudFront Distribution (global HTTPS)
resource "aws_cloudfront_distribution" "web" {
  count = local.web_enabled ? 1 : 0

  enabled             = true
  comment             = "${var.project_name} static site"
  default_root_object = "index.html"

  origin {
    domain_name = aws_s3_bucket.web[0].bucket_regional_domain_name
    origin_id   = "s3-${aws_s3_bucket.web[0].id}"

    origin_access_control_id = aws_cloudfront_origin_access_control.oac[0].id
  }

  default_cache_behavior {
    target_origin_id       = "s3-${aws_s3_bucket.web[0].id}"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]

    compress = true

    # Simple cache policy settings inline (or you can use managed IDs)
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  # Open to all countries; restrict if needed
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Use CloudFront default cert for *.cloudfront.net
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = local.common_tags
}

# Bucket policy: allow CloudFront OAC to read objects
data "aws_iam_policy_document" "web_bucket_policy" {
  count = local.web_enabled ? 1 : 0

  statement {
    sid     = "AllowCloudFrontOAC"
    effect  = "Allow"
    actions = ["s3:GetObject"]
    resources = [
      "${aws_s3_bucket.web[0].arn}/*"
    ]

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

  depends_on = [
    aws_s3_bucket_public_access_block.web
  ]
}

#############################################
# Upload built site assets to the S3 bucket #
#############################################

# Expect these files to have been copied by your build step:
#   infra/build/site/index.html
#   infra/build/site/app.js

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


#resource "aws_cloudfront_invalidation" "site_invalidation" {
# count = local.web_enabled ? 1 : 0

#distribution_id = aws_cloudfront_distribution.web[0].id
#  paths           = ["/*"]

# Ensure invalidation runs after we upload objects
# depends_on = [
#  aws_s3_object.index,
#   aws_s3_object.app
# ]
#}