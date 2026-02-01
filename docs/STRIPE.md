# Stripe sandbox testing

This document explains how to test Stripe Checkout and webhooks locally.

1. Set environment variables (example):

Windows PowerShell:
```powershell
$env:STRIPE_API_KEY="sk_test_..."
$env:STRIPE_PUBLIC_KEY="pk_test_..."
$env:STRIPE_WEBHOOK_SECRET="whsec_..."
$env:STRIPE_CURRENCY="usd"
```

2. Install dependencies and run server:

```bash
pipenv install stripe
pipenv run python manage.py runserver
```

3. Create a Checkout session by visiting a product page and clicking "Pay with Card (Stripe)".

4. Test webhooks locally using the Stripe CLI (recommended):

- Install Stripe CLI: https://stripe.com/docs/stripe-cli
- Listen and forward events to local webhook endpoint:

```bash
stripe listen --forward-to http://localhost:8000/orders/stripe/webhook/ --api-key sk_test_...
```

- When you complete a test Checkout session in the browser using Stripe test cards (e.g. `4242 4242 4242 4242`), the CLI will forward `checkout.session.completed` to your local webhook and the app will finalize the `Order`.

5. Debugging tips:
- Ensure `STRIPE_WEBHOOK_SECRET` is set to the CLI-provided signing secret (the `stripe listen` command shows it).
- Check `Order` entries in the admin to see `stripe_session_id`.
- Use the console email backend during development to view outgoing HTML emails in the console.

6. Notes:
- For production, set secure webhook endpoints and verify signatures.
- Consider persisting payment intent IDs and using them for reconciliation.
