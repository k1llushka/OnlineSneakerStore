from django.db import models


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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Заказ #{self.pk} от {self.customer_name}"

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    sneaker = models.ForeignKey(Sneaker, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=10, blank=True)

    @property
    def subtotal(self):
        return self.quantity * self.sneaker.price

