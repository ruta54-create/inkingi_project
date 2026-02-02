from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_AWAITING_CONFIRMATION = 'awaiting_confirmation'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending Payment')),
        (STATUS_AWAITING_CONFIRMATION, _('Awaiting Vendor Confirmation')),
        (STATUS_PROCESSING, _('Processing')),
        (STATUS_SHIPPED, _('Shipped')),
        (STATUS_DELIVERED, _('Delivered')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_CANCELLED, _('Cancelled')),
    ]

    # Basic order information
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    total = models.DecimalField(decimal_places=2, max_digits=12, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # Delivery information
    delivery_address = models.TextField()
    phone = models.CharField(max_length=20)
    delivery_notes = models.TextField(blank=True, null=True)

    # GPS Location for delivery
    delivery_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Payment proof
    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True,
                                       help_text='Upload screenshot/proof of payment')
    payment_proof_uploaded_at = models.DateTimeField(null=True, blank=True)

    # Vendor confirmation
    vendor_confirmed = models.BooleanField(default=False)
    vendor_confirmed_at = models.DateTimeField(null=True, blank=True)
    vendor_confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='confirmed_orders'
    )
    vendor_rejection_reason = models.TextField(blank=True, null=True)
    
    # Delivery options
    DELIVERY_STANDARD = 'standard'
    DELIVERY_EXPRESS = 'express'
    DELIVERY_PICKUP = 'pickup'
    
    DELIVERY_CHOICES = [
        (DELIVERY_STANDARD, _('Standard Delivery (3-5 days)')),
        (DELIVERY_EXPRESS, _('Express Delivery (1-2 days)')),
        (DELIVERY_PICKUP, _('Store Pickup')),
    ]
    
    delivery_option = models.CharField(
        max_length=20, 
        choices=DELIVERY_CHOICES, 
        default=DELIVERY_STANDARD
    )
    delivery_cost = models.DecimalField(
        decimal_places=2, 
        max_digits=10, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Payment information
    PAYMENT_BANK = 'bank'
    PAYMENT_MOMO = 'momo'
    PAYMENT_AIRTEL = 'airtel'
    PAYMENT_TIGO = 'tigo'
    PAYMENT_CARD = 'card'
    PAYMENT_CASH = 'cash'
    
    PAYMENT_CHOICES = [
        (PAYMENT_BANK, _('Bank Transfer')),
        (PAYMENT_MOMO, _('MTN Mobile Money')),
        (PAYMENT_AIRTEL, _('Airtel Money')),
        (PAYMENT_TIGO, _('Tigo Cash')),
        (PAYMENT_CARD, _('Credit/Debit Card')),
        (PAYMENT_CASH, _('Cash on Delivery')),
    ]
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default=PAYMENT_MOMO
    )
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Timestamps
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Tracking and Tax
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    tax_rate = models.DecimalField(
        decimal_places=4, 
        max_digits=6, 
        default=0.18,  # 18% VAT for Rwanda
        validators=[MinValueValidator(0)]
    )
    tax_amount = models.DecimalField(
        decimal_places=2, 
        max_digits=10, 
        default=0,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username} - {self.total} RWF ({self.get_status_display()})"
    
    @property
    def subtotal(self):
        """Calculate subtotal without delivery cost and tax"""
        items_total = sum(item.price * item.quantity for item in self.items.all())
        return items_total
    
    @property
    def subtotal_with_delivery(self):
        """Calculate subtotal including delivery cost but without tax"""
        return self.subtotal + self.delivery_cost
    
    @property
    def calculated_tax(self):
        """Calculate tax amount based on subtotal + delivery"""
        return (self.subtotal + self.delivery_cost) * self.tax_rate
    
    @property
    def total_with_tax(self):
        """Calculate total including tax"""
        return self.subtotal + self.delivery_cost + self.calculated_tax
    
    @property
    def invoice_number(self):
        """Generate invoice number"""
        return f"INV-{self.created_at.strftime('%Y%m')}-{self.id:06d}"
    
    @property
    def formatted_tracking_number(self):
        """Generate formatted tracking number"""
        return self.tracking_number or f"TRK{self.id:08d}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate tax automatically"""
        if self.pk:  # Only calculate for existing orders with items
            self.tax_amount = self.calculated_tax
            # Update total to include tax
            self.total = self.total_with_tax
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Purchase(models.Model):
    """Record of a mock purchase (used by the Mock Checkout Process)."""
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='purchases')
    quantity = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(decimal_places=2, max_digits=12, validators=[MinValueValidator(0)])
    PAYMENT_BANK = 'bank'
    PAYMENT_MOMO = 'momo'
    PAYMENT_AIRTEL = 'airtel'
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_BANK, 'Bank Transfer'),
        (PAYMENT_MOMO, 'Momo Pay'),
        (PAYMENT_AIRTEL, 'Airtel Money'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_BANK)
    transaction_id = models.CharField(max_length=128, blank=True, null=True)
    refunded = models.BooleanField(default=False)
    refunded_at = models.DateTimeField(blank=True, null=True)
    refunded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refunds'
    )
    refund_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PurchaseLog(models.Model):
    ACTION_PURCHASE = 'purchase'
    ACTION_REFUND = 'refund'
    ACTION_CHOICES = [
        (ACTION_PURCHASE, 'Purchase'),
        (ACTION_REFUND, 'Refund'),
    ]

    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_display()} for Purchase #{self.purchase_id} by {self.actor} at {self.created_at}"

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Purchase #{self.id} - {self.customer.username} - {self.product.name} x{self.quantity}"


class StripeWebhookEvent(models.Model):
    """Store raw Stripe webhook events for debugging and auditing."""
    stripe_event_id = models.CharField(max_length=255, blank=True, null=True, help_text='Stripe event id (e.g. evt_...)')
    event_type = models.CharField(max_length=128, blank=True, null=True)
    payload = models.TextField(blank=True, null=True)
    headers = models.TextField(blank=True, null=True)
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='webhook_events')
    processed = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_at']

    def __str__(self):
        return f"{self.event_type or 'stripe.event'} @ {self.received_at}"
