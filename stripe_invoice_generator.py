#!/usr/bin/env python3
# /// script
# dependencies = [
#   "stripe>=7.0.0",
#   "requests>=2.25.0",
# ]
# ///
import stripe
import argparse
import os
import sys
import time
import requests
import getpass
from decimal import Decimal

def main():
    parser = argparse.ArgumentParser(description='Generate Stripe invoice and download PDF')
    parser.add_argument('--item', required=True, help='Name of the invoice item')
    parser.add_argument('--price', type=float, required=True, help='Price in USD')
    parser.add_argument('--dir', default='.', help='Directory to save PDF (default: current directory)')
    parser.add_argument('--prefix', default=f'508.dev {getpass.getuser()} Invoice-', help='Filename prefix (default: 508.dev {username} Invoice-)')
    parser.add_argument('--customer', help='Stripe customer ID (if not provided, uses STRIPE_508_INVOICE_CUSTOMER env var or finds/creates 508.dev LLC customer)')
    parser.add_argument('--template', help='Invoice template ID (if not provided, uses STRIPE_508_INVOICE_TEMPLATE env var)')
    parser.add_argument('--send-email', action='store_true', help='Send invoice email to customer (default: False)')
    parser.add_argument('--api_key', help='Stripe API key (or set STRIPE_API_KEY env var)')

    args = parser.parse_args()

    # Set up Stripe API key
    api_key = args.api_key or os.getenv('STRIPE_API_KEY')
    if not api_key:
        print("Error: Stripe API key required. Set STRIPE_API_KEY env var or use --api_key", file=sys.stderr)
        sys.exit(1)

    # Get template ID
    template_id = args.template or os.getenv('STRIPE_508_INVOICE_TEMPLATE')
    if not template_id:
        print("Error: Invoice template ID required. Set STRIPE_508_INVOICE_TEMPLATE env var or use --template", file=sys.stderr)
        sys.exit(1)

    stripe.api_key = api_key

    try:
        # Get or create customer
        customer_id = args.customer or os.getenv('STRIPE_508_INVOICE_CUSTOMER')
        if customer_id:
            print(f"Using customer: {customer_id}")
        else:
            # Find existing 508.dev LLC customer or create one
            print("Looking for 508.dev LLC customer...")
            customers = stripe.Customer.list(email='billing@508.dev', limit=1)

            if customers.data:
                customer_id = customers.data[0].id
                print(f"Found existing customer: {customer_id}")
            else:
                print("Creating new 508.dev LLC customer...")
                customer = stripe.Customer.create(
                    name='508.dev LLC',
                    email='billing@508.dev',
                    tax_exempt='exempt',
                    address={
                        'line1': '2376 Gemini St',
                        'city': 'Houston',
                        'state': 'TX',
                        'postal_code': '77058',
                        'country': 'US',
                    }
                )
                customer_id = customer.id
                print(f"Created new customer: {customer_id}")
        # Create invoice first
        print(f"Creating invoice with template {template_id}...")
        invoice = stripe.Invoice.create(
            customer=customer_id,
            auto_advance=False,  # Don't automatically finalize
            rendering={
                'template': template_id
            }
        )

        # Create invoice item attached to the invoice
        print(f"Creating invoice item: {args.item} - ${args.price}")
        invoice_item = stripe.InvoiceItem.create(
            customer=customer_id,
            invoice=invoice.id,  # Attach to specific invoice
            amount=int(args.price * 100),  # Convert to cents
            currency='usd',
            description=args.item,
        )

        # Finalize the invoice
        print("Finalizing invoice...")
        invoice = stripe.Invoice.finalize_invoice(invoice.id)

        # Send email if requested
        if args.send_email:
            print("Sending invoice email to customer...")
            stripe.Invoice.send_invoice(invoice.id)

        # Wait for PDF to be ready and download it
        print("Waiting for PDF to be generated...")
        max_attempts = 30
        for attempt in range(max_attempts):
            invoice = stripe.Invoice.retrieve(invoice.id)
            if invoice.invoice_pdf:
                print(f"PDF ready! Downloading from: {invoice.invoice_pdf}")

                # Download the PDF
                response = requests.get(invoice.invoice_pdf)

                # Expand ~ and create directory if needed
                target_dir = os.path.expanduser(args.dir)
                os.makedirs(target_dir, exist_ok=True)

                filename = os.path.join(target_dir, f"{args.prefix}{invoice.number}.pdf")

                with open(filename, 'wb') as f:
                    f.write(response.content)

                print(f"Invoice PDF saved as: {filename}")
                print(f"Invoice ID: {invoice.id}")
                print(f"Invoice Number: {invoice.number}")
                break
            else:
                time.sleep(2)
        else:
            print("Timeout waiting for PDF generation", file=sys.stderr)
            sys.exit(1)

    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()