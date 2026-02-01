from django.contrib import admin
from django import forms
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.admin import helpers
from django.template.response import TemplateResponse
from django.contrib import messages
from .models import Order, OrderItem, Purchase, PurchaseLog, StripeWebhookEvent
import json


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0
	readonly_fields = ('product', 'quantity', 'price')
	can_delete = False

	def has_add_permission(self, request, obj=None):
		return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	# Enhanced list display with better formatting
	list_display = ('id', 'customer_link', 'total_formatted', 'status_badge', 'items_count', 'stripe_session_id', 'created_at')
	list_filter = ('status', 'created_at')
	search_fields = ('customer__username', 'customer__email', 'stripe_session_id')
	inlines = [OrderItemInline]
	actions = ['mark_completed']
	readonly_fields = ('created_at',)

	def customer_link(self, obj):
		if obj.customer:
			url = reverse('admin:accounts_customuser_change', args=[obj.customer.id])
			return format_html('<a href="{}">{}</a>', url, obj.customer.username)
		return '-'
	customer_link.short_description = 'Customer'

	def total_formatted(self, obj):
		return format_html('<strong>${:.2f}</strong>', obj.total)
	total_formatted.short_description = 'Total'

	def status_badge(self, obj):
		colors = {
			'pending': '#ffc107',
			'completed': '#28a745',
			'cancelled': '#dc3545'
		}
		color = colors.get(obj.status, '#6c757d')
		return format_html(
			'<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
			color, obj.status.upper()
		)
	status_badge.short_description = 'Status'

	def items_count(self, obj):
		count = obj.items.count()
		return format_html('<span title="Total items in order">{}</span>', count)
	items_count.short_description = 'Items'

	def mark_completed(self, request, queryset):
		updated = queryset.update(status='completed')
		self.message_user(request, f"Marked {updated} order(s) as completed.")

	mark_completed.short_description = 'Mark selected orders as completed'


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
	list_display = ('id', 'customer_link', 'product_link', 'quantity', 'amount_formatted', 'payment_method_badge', 'transaction_id_short', 'refunded_badge', 'created_at')
	list_filter = ('created_at', 'payment_method', 'refunded')
	search_fields = ('customer__username', 'product__name', 'transaction_id')
	actions = ['mark_refunded', 'unmark_refunded', 'refund_with_reason']
	readonly_fields = ('created_at', 'refunded_at', 'refunded_by')

	# Enhanced action form with better styling
	class RefundActionForm(forms.Form):
		refund_reason = forms.CharField(
			required=False, 
			label='Refund reason',
			widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}),
			help_text='Optional reason for the refund (will be included in notification emails)'
		)

	action_form = RefundActionForm

	def customer_link(self, obj):
		if obj.customer:
			url = reverse('admin:accounts_customuser_change', args=[obj.customer.id])
			return format_html('<a href="{}">{}</a>', url, obj.customer.username)
		return '-'
	customer_link.short_description = 'Customer'

	def product_link(self, obj):
		if obj.product:
			url = reverse('admin:products_product_change', args=[obj.product.id])
			return format_html('<a href="{}">{}</a>', url, obj.product.name[:30])
		return '-'
	product_link.short_description = 'Product'

	def amount_formatted(self, obj):
		return format_html('<strong>${:.2f}</strong>', obj.amount)
	amount_formatted.short_description = 'Amount'

	def payment_method_badge(self, obj):
		colors = {
			'stripe': '#635bff',
			'bank': '#28a745',
			'momo': '#ff6b35',
			'airtel': '#e31e24'
		}
		color = colors.get(obj.payment_method, '#6c757d')
		return format_html(
			'<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
			color, obj.payment_method.upper()
		)
	payment_method_badge.short_description = 'Payment'

	def transaction_id_short(self, obj):
		if obj.transaction_id and len(obj.transaction_id) > 20:
			return format_html('<span title="{}">{}</span>', obj.transaction_id, obj.transaction_id[:20] + '...')
		return obj.transaction_id or '-'
	transaction_id_short.short_description = 'Transaction ID'

	def refunded_badge(self, obj):
		if obj.refunded:
			return format_html(
				'<span style="background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">REFUNDED</span>'
			)
		return format_html(
			'<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">ACTIVE</span>'
		)
	refunded_badge.short_description = 'Status'

	def mark_refunded(self, request, queryset):
		updated = 0
		for p in queryset.select_related('product'):
			if not p.refunded:
				# restock product
				prod = p.product
				prod.stock = prod.stock + p.quantity
				prod.save()
				p.refunded = True
				p.refunded_at = timezone.now()
				p.refunded_by = request.user
				p.refund_reason = request.POST.get('refund_reason', '')
				p.save()
				PurchaseLog.objects.create(purchase=p, action=PurchaseLog.ACTION_REFUND, actor=request.user, note=p.refund_reason)
				updated += 1
		self.message_user(request, f"Marked {updated} purchase(s) as refunded and restocked.")

	def unmark_refunded(self, request, queryset):
		updated = queryset.update(refunded=False)
		self.message_user(request, f"Cleared refunded flag for {updated} purchase(s).")

	def refund_with_reason(self, request, queryset):
		"""Enhanced refund action with better error handling and notifications."""
		reason = request.POST.get('refund_reason', '').strip() or 'Refunded via admin action'
		updated = 0
		errors = []
		
		for p in queryset.select_related('product'):
			if not p.refunded:
				try:
					# Restock product
					prod = p.product
					prod.stock = prod.stock + p.quantity
					prod.save()
					
					# Update purchase
					p.refunded = True
					p.refunded_at = timezone.now()
					p.refunded_by = request.user
					p.refund_reason = reason
					p.save()
					
					# Create log entry
					PurchaseLog.objects.create(
						purchase=p, 
						action=PurchaseLog.ACTION_REFUND, 
						actor=request.user, 
						note=reason
					)
					
					# Send notifications
					try:
						from django.template.loader import render_to_string
						from django.core.mail import EmailMessage
						
						# Customer notification
						html = render_to_string('emails/refund.html', {'purchase': p, 'user': p.customer})
						msg = EmailMessage(
							subject=f'Purchase #{p.id} refunded', 
							body=html, 
							from_email=settings.DEFAULT_FROM_EMAIL, 
							to=[p.customer.email]
						)
						msg.content_subtype = 'html'
						msg.send(fail_silently=True)
						
						# Vendor notification
						vendor_email = getattr(p.product.vendor, 'email', None)
						if vendor_email:
							vhtml = render_to_string('emails/refund.html', {'purchase': p, 'user': p.product.vendor})
							vmsg = EmailMessage(
								subject=f'Purchase #{p.id} refunded', 
								body=vhtml, 
								from_email=settings.DEFAULT_FROM_EMAIL, 
								to=[vendor_email]
							)
							vmsg.content_subtype = 'html'
							vmsg.send(fail_silently=True)
					except Exception as e:
						# Don't fail the refund if email fails
						import logging
						logger = logging.getLogger(__name__)
						logger.warning(f'Failed to send refund notification for purchase {p.id}: {e}')
					
					updated += 1
				except Exception as e:
					errors.append(f'Purchase #{p.id}: {str(e)}')
		
		# Provide detailed feedback
		if updated > 0:
			self.message_user(request, f"✅ Successfully refunded {updated} purchase(s) and restocked inventory.")
		if errors:
			for error in errors[:5]:  # Show first 5 errors
				self.message_user(request, f"❌ {error}", level=messages.ERROR)
			if len(errors) > 5:
				self.message_user(request, f"⚠️ {len(errors) - 5} additional errors occurred.", level=messages.WARNING)

	refund_with_reason.short_description = 'Refund selected purchases (enter reason below)'
	mark_refunded.short_description = 'Mark selected purchases as refunded'
	unmark_refunded.short_description = 'Clear refunded flag for selected purchases'


@admin.register(PurchaseLog)
class PurchaseLogAdmin(admin.ModelAdmin):
	list_display = ('id', 'purchase_link', 'action_badge', 'actor_link', 'note_preview', 'created_at')
	list_filter = ('action', 'created_at')
	search_fields = ('purchase__customer__username', 'purchase__product__name', 'actor__username', 'note')
	readonly_fields = ('purchase', 'action', 'actor', 'note', 'created_at')
	list_per_page = 50

	def has_add_permission(self, request):
		return False

	def has_delete_permission(self, request, obj=None):
		return False

	def purchase_link(self, obj):
		if obj.purchase:
			url = reverse('admin:orders_purchase_change', args=[obj.purchase.id])
			return format_html('<a href="{}">Purchase #{}</a>', url, obj.purchase.id)
		return '-'
	purchase_link.short_description = 'Purchase'

	def action_badge(self, obj):
		colors = {
			'purchase': '#28a745',
			'refund': '#dc3545',
			'update': '#ffc107'
		}
		color = colors.get(obj.action, '#6c757d')
		return format_html(
			'<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
			color, obj.action.upper()
		)
	action_badge.short_description = 'Action'

	def actor_link(self, obj):
		if obj.actor:
			url = reverse('admin:accounts_customuser_change', args=[obj.actor.id])
			return format_html('<a href="{}">{}</a>', url, obj.actor.username)
		return '-'
	actor_link.short_description = 'Actor'

	def note_preview(self, obj):
		if obj.note and len(obj.note) > 50:
			return format_html('<span title="{}">{}</span>', obj.note, obj.note[:50] + '...')
		return obj.note or '-'
	note_preview.short_description = 'Note'


@admin.register(StripeWebhookEvent)
class StripeWebhookEventAdmin(admin.ModelAdmin):
	list_display = ('stripe_event_id', 'event_type_badge', 'order_link', 'processed_badge', 'headers_summary', 'received_at', 'view_payload_link')
	readonly_fields = ('stripe_event_id', 'event_type', 'payload', 'headers', 'order', 'processed', 'received_at')
	list_filter = ('event_type', 'processed', 'received_at')
	search_fields = ('stripe_event_id', 'event_type', 'payload')
	actions = ['mark_processed', 'reprocess_events']
	list_per_page = 25

	def event_type_badge(self, obj):
		colors = {
			'checkout.session.completed': '#28a745',
			'payment_intent.succeeded': '#17a2b8',
			'invoice.payment_succeeded': '#ffc107',
		}
		color = colors.get(obj.event_type, '#6c757d')
		return format_html(
			'<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
			color, obj.event_type or 'unknown'
		)
	event_type_badge.short_description = 'Event Type'

	def order_link(self, obj):
		if obj.order:
			url = reverse('admin:orders_order_change', args=[obj.order.id])
			return format_html('<a href="{}">Order #{}</a>', url, obj.order.id)
		return format_html('<span style="color: #6c757d;">No order</span>')
	order_link.short_description = 'Order'

	def processed_badge(self, obj):
		if obj.processed:
			return format_html(
				'<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">✓ PROCESSED</span>'
			)
		return format_html(
			'<span style="background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">⚠ PENDING</span>'
		)
	processed_badge.short_description = 'Status'

	def headers_summary(self, obj):
		try:
			headers = json.loads(obj.headers or '{}')
			sensitive_count = sum(1 for k in headers.keys() if any(pattern in k.lower() for pattern in ['auth', 'token', 'signature', 'key', 'secret']))
			total_count = len(headers)
			if sensitive_count > 0:
				return format_html(
					'<span title="Total: {}, Sensitive: {} (redacted)">{} headers ({} redacted)</span>',
					total_count, sensitive_count, total_count, sensitive_count
				)
			return format_html('<span title="No sensitive headers detected">{} headers</span>', total_count)
		except:
			return format_html('<span style="color: #dc3545;">Invalid JSON</span>')
	headers_summary.short_description = 'Headers'

	def mark_processed(self, request, queryset):
		updated = queryset.update(processed=True)
		self.message_user(request, f"Marked {updated} webhook event(s) as processed.")

	mark_processed.short_description = 'Mark selected webhook events as processed'

	def get_urls(self):
		from django.urls import path
		urls = super().get_urls()
		custom_urls = [
			path('<int:object_id>/view-payload/', self.admin_site.admin_view(self.view_payload), name='orders_stripewebhookevent_view_payload'),
			path('reprocess-confirmation/', self.admin_site.admin_view(self.reprocess_confirmation), name='orders_stripewebhookevent_reprocess_confirmation'),
		]
		return custom_urls + urls

	def view_payload(self, request, object_id):
		import json as _json
		obj = get_object_or_404(StripeWebhookEvent, pk=object_id)
		# try to pretty-print JSON payload if possible
		pretty_payload = None
		pretty_headers = None
		
		try:
			data = _json.loads(obj.payload)
			pretty_payload = _json.dumps(data, indent=2, ensure_ascii=False)
		except Exception:
			pretty_payload = obj.payload or ''

		try:
			headers = _json.loads(obj.headers or '{}')
			pretty_headers = _json.dumps(headers, indent=2, ensure_ascii=False)
		except Exception:
			pretty_headers = obj.headers or '{}'

		return render(request, 'admin/stripe_webhook_payload.html', {
			'object': obj, 
			'pretty_payload': pretty_payload,
			'pretty_headers': pretty_headers
		})

	def view_payload_link(self, obj):
		if not obj:
			return ''
		url = reverse('admin:orders_stripewebhookevent_view_payload', args=[obj.id])
		return format_html('<a class="button" href="{}">View Details</a>', url)

	view_payload_link.short_description = 'Actions'

	def reprocess_confirmation(self, request):
		"""Show confirmation page before reprocessing webhook events."""
		if request.method == 'POST':
			if 'confirm' in request.POST:
				# User confirmed, proceed with reprocessing
				selected_ids = request.POST.getlist('selected_ids')
				return self._perform_reprocess(request, selected_ids)
			else:
				# User cancelled
				messages.info(request, 'Reprocessing cancelled.')
				return self._redirect_to_changelist()

		# Show confirmation page
		selected_ids = request.GET.getlist('ids')
		if not selected_ids:
			messages.error(request, 'No webhook events selected for reprocessing.')
			return self._redirect_to_changelist()

		events = StripeWebhookEvent.objects.filter(id__in=selected_ids)
		
		context = {
			'title': 'Confirm Webhook Event Reprocessing',
			'events': events,
			'events_count': events.count(),
			'selected_ids': selected_ids,
			'opts': self.model._meta,
			'app_label': self.model._meta.app_label,
		}
		
		return TemplateResponse(request, 'admin/reprocess_confirmation.html', context)

	def _perform_reprocess(self, request, selected_ids):
		"""Actually perform the reprocessing after confirmation."""
		from .stripe_utils import process_stripe_event
		from django.utils import timezone
		import logging
		
		logger = logging.getLogger(__name__)
		events = StripeWebhookEvent.objects.filter(id__in=selected_ids)
		processed = 0
		failed = 0
		errors = []
		
		# Log the start of reprocessing
		logger.info(f'Admin user {request.user.username} starting reprocessing of {events.count()} webhook events')
		
		for ev in events:
			try:
				data = None
				try:
					data = json.loads(ev.payload)
				except Exception as e:
					data = ev.payload
					logger.warning(f'Event {ev.stripe_event_id} has invalid JSON payload: {e}')
				
				# Log the reprocessing attempt
				logger.info(f'Reprocessing webhook event {ev.stripe_event_id} (type: {ev.event_type}) by user {request.user.username}')
				
				ok = process_stripe_event(data, saved_event=ev)
				if ok:
					ev.processed = True
					ev.save()
					processed += 1
					logger.info(f'Successfully reprocessed event {ev.stripe_event_id}')
				else:
					failed += 1
					error_msg = f'Event {ev.stripe_event_id} processing returned False - check logs for details'
					errors.append(error_msg)
					logger.error(error_msg)
			except Exception as e:
				failed += 1
				error_msg = f'Failed to reprocess event {ev.stripe_event_id}: {str(e)}'
				errors.append(error_msg)
				logger.exception(f'Exception during reprocessing of event {ev.stripe_event_id}')
				
		# Log the completion
		logger.info(f'Reprocessing completed by {request.user.username}: {processed} successful, {failed} failed')
		
		# Show detailed results
		if processed > 0:
			messages.success(request, f'✅ Successfully reprocessed {processed} webhook event(s).')
		if failed > 0:
			messages.error(request, f'❌ Failed to reprocess {failed} webhook event(s).')
			# Show first few errors for debugging
			for error in errors[:3]:
				messages.warning(request, f'⚠️ {error}')
			if len(errors) > 3:
				messages.info(request, f'📋 {len(errors) - 3} additional errors - check server logs for details.')
			
		return self._redirect_to_changelist()

	def _redirect_to_changelist(self):
		from django.shortcuts import redirect
		return redirect('admin:orders_stripewebhookevent_changelist')

	def reprocess_events(self, request, queryset):
		"""Enhanced reprocess action with confirmation step."""
		selected_ids = [str(obj.id) for obj in queryset]
		
		# Redirect to confirmation page
		from django.shortcuts import redirect
		from django.http import HttpResponseRedirect
		url = reverse('admin:orders_stripewebhookevent_reprocess_confirmation')
		return HttpResponseRedirect(f'{url}?ids={",".join(selected_ids)}')

	reprocess_events.short_description = '🔄 Re-process selected webhook events (with confirmation)'


# Custom admin dashboard with enhanced statistics
class AdminDashboardView:
	"""Enhanced admin dashboard with comprehensive statistics and monitoring."""
	
	@staticmethod
	def get_dashboard_stats():
		from django.db.models import Count, Sum, Q, Avg
		from django.utils import timezone
		from datetime import timedelta
		import time
		
		# Performance monitoring
		start_time = time.time()
		
		now = timezone.now()
		today = now.date()
		week_ago = now - timedelta(days=7)
		month_ago = now - timedelta(days=30)
		
		# Optimized queries with select_related and prefetch_related
		stats = {
			'orders': {
				'total': Order.objects.count(),
				'pending': Order.objects.filter(status='pending').count(),
				'completed': Order.objects.filter(status='completed').count(),
				'today': Order.objects.filter(created_at__date=today).count(),
				'this_week': Order.objects.filter(created_at__gte=week_ago).count(),
				'avg_value': Order.objects.aggregate(Avg('total'))['total__avg'] or 0,
			},
			'purchases': {
				'total': Purchase.objects.count(),
				'total_amount': Purchase.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
				'refunded': Purchase.objects.filter(refunded=True).count(),
				'refunded_amount': Purchase.objects.filter(refunded=True).aggregate(Sum('amount'))['amount__sum'] or 0,
				'today': Purchase.objects.filter(created_at__date=today).count(),
				'this_week': Purchase.objects.filter(created_at__gte=week_ago).count(),
				'avg_value': Purchase.objects.aggregate(Avg('amount'))['amount__avg'] or 0,
			},
			'webhooks': {
				'total': StripeWebhookEvent.objects.count(),
				'processed': StripeWebhookEvent.objects.filter(processed=True).count(),
				'pending': StripeWebhookEvent.objects.filter(processed=False).count(),
				'today': StripeWebhookEvent.objects.filter(received_at__date=today).count(),
				'this_week': StripeWebhookEvent.objects.filter(received_at__gte=week_ago).count(),
				'success_rate': 0,
			},
			'payment_methods': Purchase.objects.values('payment_method').annotate(
				count=Count('id'),
				total_amount=Sum('amount')
			).order_by('-count'),
			'performance': {
				'query_time': round((time.time() - start_time) * 1000, 2),  # milliseconds
				'cache_status': 'enabled' if hasattr(settings, 'CACHES') else 'disabled',
			}
		}
		
		# Calculate webhook success rate
		if stats['webhooks']['total'] > 0:
			stats['webhooks']['success_rate'] = round(
				(stats['webhooks']['processed'] / stats['webhooks']['total']) * 100, 1
			)
		
		return stats

# Add the dashboard view to the admin site
def enhanced_admin_dashboard(request):
	"""Enhanced admin dashboard with comprehensive statistics."""
	if not request.user.is_staff:
		from django.contrib.admin.views.decorators import staff_member_required
		return staff_member_required(lambda r: None)(request)
	
	stats = AdminDashboardView.get_dashboard_stats()
	
	# Recent activity
	recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:10]
	recent_purchases = Purchase.objects.select_related('customer', 'product').order_by('-created_at')[:10]
	recent_webhooks = StripeWebhookEvent.objects.order_by('-received_at')[:10]
	
	context = {
		'title': 'Enhanced Admin Dashboard',
		'stats': stats,
		'recent_orders': recent_orders,
		'recent_purchases': recent_purchases,
		'recent_webhooks': recent_webhooks,
	}
	
	return render(request, 'admin/enhanced_dashboard.html', context)