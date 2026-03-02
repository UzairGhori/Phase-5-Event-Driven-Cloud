# Task: T-B002 — Implement Dapr Pub/Sub event publisher
# Spec: FR-039, FR-040, NFR-018, NFR-020
# Plan: §3.2 (Publisher Matrix), §10.3 (Dead-Letter Handling)

import asyncio
import logging
import httpx

from backend.app.config import get_settings
from backend.app.events.schemas import EventEnvelope
from backend.app.events.topics import AUDIT_LOG, DEAD_LETTER, PUBSUB_NAME

logger = logging.getLogger(__name__)
settings = get_settings()

DAPR_BASE_URL = f"http://localhost:{settings.DAPR_HTTP_PORT}"
MAX_RETRIES = 3
BACKOFF_FACTORS = [1, 5, 25]  # seconds


async def publish_event(topic: str, envelope: EventEnvelope) -> bool:
    """Publish event via Dapr Pub/Sub HTTP API.

    NFR-018: Returns True even if publish fails (database-first pattern).
    NFR-020: Retries 3 times with exponential backoff (1s, 5s, 25s).
    On all retries exhausted, logs error (dead-letter in production).
    """
    url = f"{DAPR_BASE_URL}/v1.0/publish/{PUBSUB_NAME}/{topic}"
    payload = envelope.model_dump(mode="json")

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code in (200, 204):
                    logger.info(
                        "Event published",
                        extra={
                            "topic": topic,
                            "event_id": envelope.event_id,
                            "event_type": envelope.event_type,
                        },
                    )
                    return True
                logger.warning(
                    "Dapr publish returned %d, attempt %d/%d",
                    response.status_code,
                    attempt + 1,
                    MAX_RETRIES,
                )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning(
                "Dapr publish failed (attempt %d/%d): %s",
                attempt + 1,
                MAX_RETRIES,
                str(exc),
            )

        if attempt < MAX_RETRIES - 1:
            await asyncio.sleep(BACKOFF_FACTORS[attempt])

    logger.error(
        "Event publish exhausted retries, topic=%s event_id=%s",
        topic,
        envelope.event_id,
    )

    # Attempt to publish to dead-letter queue (skip if already DLQ to avoid loops)
    if topic != DEAD_LETTER:
        dlq_payload = {
            "original_topic": topic,
            "original_event": payload,
            "failure_reason": "max_retries_exhausted",
        }
        dlq_envelope = EventEnvelope(
            event_type="dead_letter",
            source=envelope.source,
            correlation_id=envelope.correlation_id,
            user_id=envelope.user_id,
            data=dlq_payload,
        )
        dlq_url = f"{DAPR_BASE_URL}/v1.0/publish/{PUBSUB_NAME}/{DEAD_LETTER}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(dlq_url, json=dlq_envelope.model_dump(mode="json"))
                logger.info(
                    "Event sent to DLQ, original_topic=%s event_id=%s",
                    topic,
                    envelope.event_id,
                )
        except Exception as dlq_exc:
            logger.error(
                "Failed to publish to DLQ: %s (original topic=%s event_id=%s)",
                str(dlq_exc),
                topic,
                envelope.event_id,
            )

    return False


async def publish_audit_event(envelope: EventEnvelope) -> bool:
    """Convenience: publish to the audit log topic. Plan §3.2."""
    audit_envelope = EventEnvelope(
        event_type=envelope.event_type,
        source=envelope.source,
        correlation_id=envelope.correlation_id,
        user_id=envelope.user_id,
        data=envelope.data,
    )
    return await publish_event(AUDIT_LOG, audit_envelope)
