# Vanity Numbers on Amazon Connect

## Overview
This project demonstrates how to extend **Amazon Connect** with a custom vanity number service.  
When a customer calls, their phone number is converted into **vanity word combinations**.  
The system stores the top 5 options in DynamoDB, speaks the top 3 back to the caller, and also exposes them via a simple **web app**.

Deliverables:
- AWS Lambda (vanity processor, API)
- DynamoDB table for storing results
- Amazon Connect Contact Flow + Phone Number
- Infrastructure as Code (Terraform)
- Static web app (CloudFront + S3) showing the last 5 callers
- Logging, tracing, and metrics via AWS Lambda Powertools

---

## Architecture

```mermaid
flowchart LR
  Caller[Inbound Caller] -->|PSTN| Connect[Amazon Connect Contact Flow]
  Connect -->|Invoke Lambda| VanityLambda[Lambda: Vanity Processor]
  VanityLambda -->|PutItem| DDB[(DynamoDB\nVanityCalls Table)]
  VanityLambda -->|Return 3 options| Connect

  Web[Browser] --> CF[CloudFront Distribution]
  CF --> S3[S3 Static Site\nindex.html + app.js]
  Web -->|GET /last5| API[API Gateway HTTP API]
  API --> ApiLambda[Lambda: API /last5]
  ApiLambda -->|Query last 5| DDB

  subgraph Observability
    VanityLambda -.-> Logs[CloudWatch Logs]
    VanityLambda -.-> XRay[X-Ray]
    VanityLambda -.-> Metrics[CloudWatch Metrics]
    ApiLambda -.-> Logs
    ApiLambda -.-> XRay
    ApiLambda -.-> Metrics
  end
 ``` 

## “Best” Vanity (Scoring)
- Prefer longest trailing real word (e.g., `FLOWERS` over `FLOW`).
- Prefer more letters (fewer leftover digits), bonus for memorable repeats.
- Small penalty if digits `0` or `1` appear in the suffix (no letters).

## Prereqs
- AWS account with **Amazon Connect** instance and a claimed phone number.
- AWS CLI, Terraform ≥ 1.6, Python 3.12, `pip`, `zip`.

## Build & Deploy

```bash
# From repo root
rm -rf infra/build && mkdir -p infra/build tmp tmp_api infra/build/site

# Vanity Lambda
cd lambda
pip install -r requirements.txt -t ../tmp
cp handler.py vanity.py model.py observability.py words_small.txt ../tmp/
cd ../tmp && zip -r ../infra/build/lambda_vanity.zip . && cd ..

# API Lambda
cp bonus-webapp/api_handler.py tmp_api/
cd tmp_api && zip -r ../infra/build/lambda_api.zip . && cd ..

# Web site
cp web/index.html infra/build/site/
cp web/app.js infra/build/site/

# Terraform
cd infra/terraform
terraform init
terraform apply -var="connect_instance_id=YOUR-CONNECT-INSTANCE-ID"
```
amazon-connect-6dee75a2f270/connect/martin-vanity-numbers

/aws/connect/martin-vanity-numbers

website  - https://d3rbp6ukovyfhw.cloudfront.net/