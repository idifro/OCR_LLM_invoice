# Invoice and Packing List Processor with ASN API Integration

This application extracts structured data from invoice and packing list PDFs using Azure OpenAI's GPT-4.1 vision capabilities and sends the processed data to an ASN API for further processing.

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
- Sends extracted data to ASN API for further processing
- Provides a REST API server for PDF processing
- Includes an API client for making requests to the server
- Uses environment variables for easy configuration

## Installation

1. Clone the repository

2. Set up your environment variables by copying the example file and updating it:

```
cp .env.example .env
```

Edit the `.env` file with your specific configuration (Azure OpenAI API key, ASN API token, etc.)

3. Install the required dependencies:

```
pip install -r requirements.txt
```

**Note:** This application requires Poppler for PDF processing:
- On Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases and add the bin directory to your PATH
- On Linux: `sudo apt-get install poppler-utils`

## Usage

### Command Line Processing

Process a PDF file directly and send to ASN API:

```
python app.py path/to/your/invoice.pdf
```

Specify a custom output path for the extracted data:

```
python app.py path/to/your/invoice.pdf --output results.json
```

Skip sending data to the ASN API:

```
python app.py path/to/your/invoice.pdf --no-api
```

### API Server

Start the FastAPI server:

```
python api_server.py
```

The API will be available at:
- http://localhost:8000/ (health check)
- http://localhost:8000/process-pdf/ (PDF processing endpoint)

### API Client

Send a PDF to the API server for processing:

```
python api_client.py path/to/your/invoice.pdf
```

Save the API response to a file:

```
python api_client.py path/to/your/invoice.pdf --output results.json
```

Specify a different API server URL:

```
python api_client.py path/to/your/invoice.pdf --api-url http://your-server:port/process-pdf/
```

## Configuration

The application uses environment variables for configuration, which can be set in the `.env` file:

```
# Azure OpenAI Configuration
MODEL_BASE_URL=https://your-endpoint.cognitiveservices.azure.com/
API_VERSION=2024-12-01-preview
MODEL_NAME=gpt-4.1
API_KEY=your_api_key_here

# ASN API Configuration
ASN_API_URL=https://asn.mazedemo.in/api/method/asn_web.purchaseinvoiceandpacking.split_and_create_docs
ASN_API_TOKEN=your_token_here

# Temp folder configuration
TEMP_OUTPUT_FOLDER=/path/to/temp/folder

# API Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG_MODE=True
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
