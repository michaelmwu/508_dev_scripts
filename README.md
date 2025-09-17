# Scripts for 508.dev

## Stripe Invoice Generator

Creates an invoice to 508.dev via Stripe and downloads the PDF.

## Setup

1. Create an invoice template in Stripe Dashboard → Settings → Invoice Template
2. Note the template ID (starts with `inrtem_`)

## Usage

Run with `uv`, `pipx`, or `pip-run`.

```bash
uv run stripe_invoice_generator.py --item "Work on Project August 2025" --price 150.00 --template inrtem_XXXX --api_key STRIPE_LIVE_KEY
```

### Full Example
```bash
uv run stripe_invoice_generator.py \
  --item "Work on Project August 2025" \
  --price 30 \
  --prefix "508.dev Michael Wu Invoice-" \
  --template inrtem_XXXX \
  --dir "~/Downloads"
```

## Arguments

- `--item` (required): Invoice item description
- `--price` (required): Price in USD
- `--dir`: Directory to save PDFs too (default: current directory)
- `--prefix`: Filename prefix (default: `508.dev {username} Invoice-`)
- `--customer`: Stripe customer ID (Can set via env variable: `STRIPE_508_INVOICE_CUSTOMER`) - If not specified, will create/find a 508.dev LLC customer via email billing@508.dev
- `--template`: Invoice template ID (Can set via env variable: `STRIPE_508_INVOICE_TEMPLATE`)
- `--send-email`: Send invoice email to customer (default: False)
- `--api_key`: Stripe API key (Can set via env variable: `STRIPE_API_KEY`)
