from __future__ import annotations

import uuid

from .base import CheckoutSession, PaymentProcessor, RefundResult, WebhookEvent


class StubProcessor(PaymentProcessor):
    """No-op payment processor for development and visual testing.

    Completes all operations instantly with success. No external API calls made.
    get_subscription_status reads from our own DB rather than a real processor.
    """

    def create_one_time_checkout(self, order, success_url: str, cancel_url: str) -> CheckoutSession:
        session_id = f"stub-{uuid.uuid4().hex[:12]}"
        return CheckoutSession(
            session_id=session_id,
            redirect_url=success_url,
        )

    def create_subscription_checkout(self, user, course_price, success_url: str, cancel_url: str) -> CheckoutSession:
        session_id = f"stub-sub-{uuid.uuid4().hex[:12]}"
        return CheckoutSession(
            session_id=session_id,
            redirect_url=success_url,
        )

    def cancel_subscription(self, subscription) -> bool:
        return True

    def issue_refund(self, order, amount_usd=None) -> RefundResult:
        return RefundResult(
            success=True,
            processor_refund_id=f"stub-refund-{uuid.uuid4().hex[:12]}",
        )

    def handle_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        return WebhookEvent(event_type="noop")

    def get_subscription_status(self, subscription) -> str:
        # No external API — trust whatever status our own code has written.
        return subscription.status
