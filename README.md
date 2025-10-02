# Vanity Numbers for Amazon Connect (Python + Terraform)

**What it does:** An Amazon Connect contact flow invokes a Lambda that converts the caller’s phone number into memorable “vanity” options (e.g., `303-555-FLOWERS`). The Lambda stores the top 5 in DynamoDB and returns the top 3 for Connect to speak. A bonus web app shows the last 5 callers.

## Architecture
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and the diagram in `docs/diagram.png`.

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