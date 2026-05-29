from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CheckoutSession:
    session_id: str
    redirect_url: str


@dataclass
class WebhookEvent:
    event_type: str
    # payment_complete | payment_failed | subscription_renewed
    # | subscription_cancelled | subscription_past_due
    processor_order_id: str | None = None
    processor_subscription_id: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class RefundResult:
    success: bool
    processor_refund_id: str | None = None
    error_message: str | None = None


class PaymentProcessor(ABC):

    @abstractmethod
    def create_one_time_checkout(self, order, success_url: str, cancel_url: str) -> CheckoutSession:
        ...

    @abstractmethod
    def create_subscription_checkout(self, user, course_price, success_url: str, cancel_url: str) -> CheckoutSession:
        ...

    @abstractmethod
    def cancel_subscription(self, subscription) -> bool:
        ...

    @abstractmethod
    def issue_refund(self, order, amount_usd=None) -> RefundResult:
        ...

    @abstractmethod
    def handle_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        ...

    @abstractmethod
    def get_subscription_status(self, subscription) -> str:
        ...
