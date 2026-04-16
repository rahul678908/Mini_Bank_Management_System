import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import BankAccount, CustomUser

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CustomUser)
def ensure_bank_account_for_customer(sender, instance: CustomUser, created: bool, **kwargs):
    """Auto-create a BankAccount whenever a customer user is saved."""
    if instance.role != "customer":
        return

    account, was_created = BankAccount.objects.get_or_create(user=instance)
    if was_created:
        logger.info(
            "Signal: BankAccount auto-created for customer %s", instance.customer_id
        )
