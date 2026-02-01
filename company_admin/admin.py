"""Company admin helpers - avoid registering models that are already registered
in the main app modules to prevent duplicate-registration errors during app autodiscover.

If you want to customize admin for Product or Purchase, do it in their respective
`products/admin.py` or `orders/admin.py` modules instead of here.
"""


