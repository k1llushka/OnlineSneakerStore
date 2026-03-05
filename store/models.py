from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.db.utils import OperationalError, ProgrammingError
from django.dispatch import receiver


class Sneaker(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    main_image = models.ImageField(upload_to="sneakers/", blank=True, null=True)
    additional_image_1 = models.ImageField(upload_to="sneakers/", blank=True, null=True)
    additional_image_2 = models.ImageField(upload_to="sneakers/", blank=True, null=True)
    sizes = models.CharField(
        max_length=255,
        help_text="Размеры через запятую, например: 40, 41, 42",
        blank=True,
    )

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"

    STATUS_CHOICES = [
        (STATUS_NEW, "Новый"),
        (STATUS_PROCESSING, "В обработке"),
        (STATUS_SHIPPED, "Отправлен"),
        (STATUS_DELIVERED, "Доставлен"),
    ]

    customer_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    address = models.CharField(max_length=500)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="store_orders",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Заказ #{self.pk} от {self.customer_name}"

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    sneaker = models.ForeignKey(Sneaker, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=10, blank=True)

    @property
    def subtotal(self):
        return self.quantity * self.sneaker.price


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    def __str__(self):
        return f"Профиль {self.user.username}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            UserProfile.objects.create(user=instance)
        except (OperationalError, ProgrammingError):
            return


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    try:
        profile, _ = UserProfile.objects.get_or_create(user=instance)
        profile.save()
    except (OperationalError, ProgrammingError):
        # UserProfile table may not exist until migrations are applied.
        return
