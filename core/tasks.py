"""
tasks.py
────────
All Celery async tasks for the core app.

Why each task exists:
  • create_notification_task   → Notifications are fire-and-forget. No reason to make
                                 the user's HTTP response wait for a DB write.
  • send_deposit_email_task    → External email/SMS calls are slow and can fail;
                                 they should never block a Stripe response.
  • send_transfer_email_task   → Same reasoning for transfer confirmations.
  • send_daily_summary_digest  → Scheduled via Celery Beat (see celery.py).
                                 Shows background scheduling knowledge.
"""

from celery import shared_task
import logging

logger = logging.getLogger(__name__)


# ─── Notification creation ────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def create_notification_task(
    self,
    user_id: int,
    transaction_id: int,
    notification_status: str,
    title: str,
    message: str,
) -> dict:
    """
    Create a Notification record asynchronously.

    Replaces every inline Notification.objects.create(...) call in views.py.
    Retries up to 3 times on failure (network blip, DB lock, etc.).
    """
    try:
        # Import inside task to avoid circular imports at module load time
        from core import models as core_models
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(id=user_id)
        transaction = core_models.Transaction.objects.get(id=transaction_id)

        notification = core_models.Notification.objects.create(
            user=user,
            transaction=transaction,
            status=notification_status,
            title=title,
            message=message,
        )

        logger.info(f"[Notification] Created #{notification.id} for user {user_id}: '{title}'")
        return {"notification_id": notification.id, "status": "created"}

    except Exception as exc:
        logger.error(f"[Notification] Task failed for user {user_id}: {exc}")
        raise self.retry(exc=exc)


# ─── Email / push notifications (async, non-blocking) ────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_deposit_email_task(self, user_id: int, amount: str, new_balance: str) -> None:
    """
    Send a deposit confirmation email after a successful Stripe payment.
    Runs after the HTTP response is already returned to the frontend.
    """
    try:
        from django.contrib.auth import get_user_model
        from django.core.mail import send_mail
        from django.conf import settings

        User = get_user_model()
        user = User.objects.get(id=user_id)

        send_mail(
            subject="Deposit Confirmed ✓",
            message=(
                f"Hi {user.username},\n\n"
                f"Your deposit of ${amount} was successful.\n"
                f"New wallet balance: ${new_balance}\n\n"
                f"Thank you for using our platform."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"[Email] Deposit confirmation sent to user {user_id}")

    except Exception as exc:
        logger.error(f"[Email] Deposit email failed for user {user_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_transfer_email_task(
    self,
    sender_id: int,
    receiver_id: int,
    amount: str,
    transfer_reference: str,
) -> None:
    """
    Notify both sender and receiver by email after a successful transfer.
    """
    try:
        from django.contrib.auth import get_user_model
        from django.core.mail import send_mail
        from django.conf import settings

        User = get_user_model()
        sender   = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)

        # Notify sender
        send_mail(
            subject="Transfer Sent ✓",
            message=(
                f"Hi {sender.username},\n\n"
                f"You sent ${amount} to {receiver.username}.\n"
                f"Reference: {transfer_reference}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[sender.email],
            fail_silently=False,
        )

        # Notify receiver
        send_mail(
            subject="You received a payment 💰",
            message=(
                f"Hi {receiver.username},\n\n"
                f"You received ${amount} from {sender.username}.\n"
                f"Reference: {transfer_reference}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[receiver.email],
            fail_silently=False,
        )

        logger.info(f"[Email] Transfer emails sent: {sender_id} → {receiver_id}, ${amount}")

    except Exception as exc:
        logger.error(f"[Email] Transfer email failed: {exc}")
        raise self.retry(exc=exc)


# ─── Scheduled: Daily digest (Celery Beat) ───────────────────────────────────

@shared_task
def send_daily_summary_digest() -> dict:
    """
    Runs every day at 08:00 (configured in celery.py beat_schedule).
    Sends each active user a summary of their wallet balance and unread notifications.
    """
    from django.contrib.auth import get_user_model
    from django.core.mail import send_mail
    from django.conf import settings
    from core import models as core_models

    User = get_user_model()
    users = User.objects.filter(is_active=True).select_related("wallet")
    sent = 0

    for user in users:
        try:
            wallet = getattr(user, "wallet", None)
            if not wallet:
                continue

            unread = core_models.Notification.objects.filter(user=user, is_read=False).count()

            send_mail(
                subject="Your Daily Wallet Summary",
                message=(
                    f"Hi {user.username},\n\n"
                    f"Balance: ${wallet.balance}\n"
                    f"Unread notifications: {unread}\n\n"
                    f"Have a great day!"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,  # Don't let one bad email abort the whole batch
            )
            sent += 1

        except Exception as e:
            logger.error(f"[Digest] Failed for user {user.id}: {e}")
            continue

    logger.info(f"[Digest] Daily summary sent to {sent} users")
    return {"sent": sent}