# Invoice and Packing List Processor

This application extracts structured data from invoice and packing list PDFs using Azure OpenAI's GPT-4.1 vision capabilities.

## Features

- Automatically converts PDF pages to images
- Detects whether each page is an invoice or packing list
- Extracts key information from invoices:
  - Vendor Name
  - Address
  - Invoice Number
  - Date
  - Line items (Order, Description, Quantity, Unit Price, Amount)
- Extracts key information from packing lists:
  - Vendor Name
  - Packing List Number
  - Address
  - Shipping Date
  - Line items (No., Order, Description, Quantity, Net Weight, Gross Weight, Measurement)
- Outputs results in structured JSON format

## Installation

1. Install the required dependencies:

```
pip install -r requirements.txt
```

## Usage

Run the application from the command line:

```
python app.py path/to/your/invoice.pdf
```

Or specify a custom output path:

```
python app.py path/to/your/invoice.pdf --output results.json
```

## Example Output

The application produces a JSON file with structured data extracted from each page of the PDF:

```json
[
  {
    "type": "invoice",
    "data": {
      "vendor_name": "Example Vendor",
      "address": "123 Main St, Anytown, USA",
      "invoice_no": "INV-12345",
      "date": "2025-01-15",
      "items": [
        {
          "order": "1",
          "description": "Product A",
          "quantity": "10",
          "unit_price": "100.00",
          "amount": "1000.00"
        },
        {
          "order": "2",
          "description": "Product B",
          "quantity": "5",
          "unit_price": "50.00",
          "amount": "250.00"
        }
      ]
    }
  },
  {
    "type": "packing_list",
    "data": {
      "vendor_name": "Example Vendor",
      "packing_list_no": "PL-12345",
      "address": "123 Main St, Anytown, USA",
      "shipping_date": "2025-01-16",
      "items": [
        {
          "no": "1",
          "order": "A001",
          "description": "Product A",
          "quantity": "10",
          "net_weight": "20kg",
          "gross_weight": "22kg",
          "measurement": "30x40x50cm"
        }
      ]
    }
  }
]
```
