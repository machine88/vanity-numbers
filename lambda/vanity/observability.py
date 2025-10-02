# lambda/vanity/observability.py
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit

# Service names show up in logs/traces/metrics
logger  = Logger(service="vanity")
tracer  = Tracer(service="vanity")
metrics = Metrics(namespace="VanityConnect")

def record_success(candidates_count: int, matched_words: int, env: str, connect_instance_id: str | None):
    """
    Emit business KPIs for a successful call processing:
      - CallsProcessed: count of processed calls
      - CandidatesGenerated: how many vanity candidates we produced
      - WordMatchRate: 1 if at least one real word matched, else 0 (as demo-friendly signal)
    Dimensions let you break metrics down by service/env/instance.
    """
    metrics.add_dimension(name="service", value="vanity")
    metrics.add_dimension(name="env", value=env or "dev")
    metrics.add_dimension(name="connectInstanceId", value=connect_instance_id or "unknown")

    metrics.add_metric(name="CallsProcessed", value=1, unit=MetricUnit.Count)
    metrics.add_metric(name="CandidatesGenerated", value=candidates_count, unit=MetricUnit.Count)

    # Simple binary match rate (demo): 1 if we matched any real word, else 0
    match_rate = 1.0 if matched_words > 0 else 0.0
    metrics.add_metric(name="WordMatchRate", value=match_rate, unit=MetricUnit.Count)

def record_error(env: str, connect_instance_id: str | None):
    """
    Emit an error counter for failed processing paths.
    """
    metrics.add_dimension(name="service", value="vanity")
    metrics.add_dimension(name="env", value=env or "dev")
    metrics.add_dimension(name="connectInstanceId", value=connect_instance_id or "unknown")
    metrics.add_metric(name="Errors", value=1, unit=MetricUnit.Count)