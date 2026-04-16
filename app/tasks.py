import logging
from decimal import Decimal

from celery import shared_task

from .models import BankAccount

# FIX: use proper logger instead of print()
logger = logging.getLogger(__name__)


@shared_task
def apply_interest_task(percent):
    """
    Apply interest to all customer account balances.
    percent: float — e.g. 10.0 for 10%
    Returns a list of dicts with customer_id and new_balance.
    """
    updated_accounts = []

    try:
        accounts = BankAccount.objects.select_related('user').all()

        for acc in accounts:
            try:
                interest = acc.balance * Decimal(str(percent)) / Decimal('100')
                acc.balance += interest
                acc.save(update_fields=['balance'])

                updated_accounts.append({
                    "customer_id": acc.user.customer_id,
                    "new_balance": float(acc.balance),
                })

                # FIX: logger.info instead of print
                logger.info(
                    "Interest applied — customer: %s | new balance: %.2f",
                    acc.user.customer_id,
                    acc.balance,
                )

            except Exception as e:
                # Log per-account errors without stopping the whole batch
                logger.error(
                    "Failed to apply interest for account id=%s: %s",
                    acc.id,
                    str(e),
                )

    except Exception as e:
        logger.error("apply_interest_task failed: %s", str(e))
        raise

    return updated_accounts