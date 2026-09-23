from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Product, StockMovement, Invoice, ReturnItem, Notification, ActivityLog
from .barcode_utils import generate_barcode_for_product


# ============================================================
# AUTO-GENERATE SKU & BARCODE
# ============================================================
@receiver(pre_save, sender=Product)
def auto_generate_sku_barcode(sender, instance, **kwargs):
    if not instance.sku:
        today = timezone.now().strftime('%Y%m%d')
        last_product = Product.objects.order_by('-id').first()
        next_id = (last_product.id + 1) if last_product else 1
        instance.sku = f"SKU-{today}-{next_id:04d}"

    if not instance.barcode:
        import random
        while True:
            candidate = ''.join([str(random.randint(0, 9)) for _ in range(13)])
            if not Product.objects.filter(barcode=candidate).exists():
                instance.barcode = candidate
                break


# ============================================================
# AUTO-GENERATE BARCODE/QR IMAGES
# ============================================================
@receiver(post_save, sender=Product)
def generate_barcode_qr_on_create(sender, instance, created, **kwargs):
    if created and (not instance.barcode_image or not instance.qr_code):
        try:
            generate_barcode_for_product(instance)
        except Exception as e:
            print(f"Auto barcode/QR error: {e}")


# ============================================================
# LOW STOCK ALERTS
# ============================================================
@receiver(post_save, sender=Product)
def product_stock_alert(sender, instance, created, **kwargs):
    if instance.quantity <= instance.low_stock_threshold:
        if instance.quantity <= 0:
            title = f"OUT OF STOCK: {instance.name}"
            message = f"'{instance.name}' is completely out of stock."
        else:
            title = f"LOW STOCK: {instance.name}"
            message = f"'{instance.name}' is running low. Current stock: {instance.quantity}"

        recipients = User.objects.filter(is_staff=True) | User.objects.filter(is_superuser=True)
        for user in recipients.distinct():
            exists = Notification.objects.filter(
                user=user, title__icontains=instance.name, is_read=False
            ).exists()
            if not exists:
                Notification.objects.create(user=user, title=title, message=message)


# ============================================================
# INVOICE CREATED LOG
# ============================================================
@receiver(post_save, sender=Invoice)
def invoice_created_log(sender, instance, created, **kwargs):
    if created and instance.created_by:
        ActivityLog.objects.create(
            user=instance.created_by,
            action=f'Created invoice {instance.invoice_number}',
            module='Sales'
        )