import os
import json
import base64
import requests
from PIL import Image
import io
import argparse
from pdf2image import convert_from_path
import tempfile
import dotenv

# Load environment variables from .env file if it exists
dotenv.load_dotenv()

# Azure OpenAI Configuration
MODEL_BASE_URL = os.getenv("MODEL_BASE_URL", "https://mha2c-mabd2a4o-eastus2.cognitiveservices.azure.com/")
API_VERSION = os.getenv("API_VERSION", "2024-12-01-preview")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1")
API_KEY = os.getenv("API_KEY", "dLbxCKdmrveV42xGDQQKOZ7PEnoXtjTASJET6JK1cdovLAk7WCvtJQQJ99BEACHYHv6XJ3w3AAAAACOG8UMJ")

class InvoiceProcessor:
    def __init__(self):
        self.base_url = MODEL_BASE_URL
        self.api_version = API_VERSION
        self.model_name = MODEL_NAME
        self.api_key = API_KEY
        
    def pdf_to_images(self, pdf_path):
        """Convert PDF to list of PIL Images using pdf2image"""
        try:
            # Create a temporary directory for pdf2image
            with tempfile.TemporaryDirectory() as path:
                # Convert PDF to a list of images
                images = convert_from_path(
                    pdf_path,
                    dpi=300,  # Higher DPI for better quality
                    output_folder="C:/Users/Harshavardhan A/Downloads/MazeWorks/OCR App/",
                    fmt="png",
                    use_pdftocairo=True,
                    single_file=False
                )
                return images
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            return []
    
    def encode_image(self, image):
        """Encode PIL Image to base64"""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def analyze_invoice_image(self, image):
        """Analyze invoice image using Azure OpenAI"""
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Convert image to base64
        base64_image = self.encode_image(image)
        
        # Create payload for the API request
        payload = {
            "messages": [
                {
                    "role": "system", 
                    "content": "You are an AI specialized in extracting structured information from invoice images. Extract information in a structured JSON format without any explanations."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract the following information from this invoice image and return it in a valid JSON format:\n\n1. Vendor Name\n2. Address\n3. Invoice No.\n4. Invoice Name\n5. Date\n6. Table containing Order, Description, Quantity, Unit Price, Amount\n7. Total Quantity\n8. Total Amount\n\nThe JSON should have keys: vendor_name, address, invoice_no, invoice_name, date, total_quantity, total_amount, and items (an array of objects with order, description, quantity, unit_price, amount)."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "model": self.model_name,
            "max_tokens": 4000
        }
        
        # Make the API request
        api_endpoint = f"{self.base_url}openai/deployments/{self.model_name}/chat/completions?api-version={self.api_version}"
        response = requests.post(api_endpoint, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            try:
                # Extract JSON from the response content
                json_str = result["choices"][0]["message"]["content"]
                # Try to parse the JSON response
                extracted_data = json.loads(json_str)
                return {"type": "invoice", "data": extracted_data}
            except (json.JSONDecodeError, KeyError) as e:
                return {"error": f"Failed to parse JSON response: {str(e)}", "raw_response": result}
        else:
            return {"error": f"API request failed with status code {response.status_code}", "details": response.text}
    
    def analyze_packing_list_image(self, image):
        """Analyze packing list image using Azure OpenAI"""
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Convert image to base64
        base64_image = self.encode_image(image)
        
        # Create payload for the API request
        payload = {
            "messages": [
                {
                    "role": "system", 
                    "content": "You are an AI specialized in extracting structured information from packing list images. Extract information in a structured JSON format without any explanations."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract the following information from this packing list image and return it in a valid JSON format:\n\n1. Vendor Name\n2. Packing List No.\n3. Packet List Name\n4. Address\n5. Shipping Date\n6. Table containing No., Order, Description, Quantity, Net Weight, Gross Weight, Measurement\n7. Total Net Weight\n8. Total Gross Weight\n9. Total Measurement\n10. Final Item name\nThe JSON should have keys: vendor_name, packing_list_no, packing_list_name, address, shipping_date, total_net_weight, total_gross_weight, total_measurement, final_item_name, and items (an array of objects with no, order, description, quantity, net_weight, gross_weight, measurement)."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "model": self.model_name,
            "max_tokens": 4000
        }
        
        # Make the API request
        api_endpoint = f"{self.base_url}openai/deployments/{self.model_name}/chat/completions?api-version={self.api_version}"
        response = requests.post(api_endpoint, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            try:
                # Extract JSON from the response content
                json_str = result["choices"][0]["message"]["content"]
                # Try to parse the JSON response
                extracted_data = json.loads(json_str)
                return {"type": "packing_list", "data": extracted_data}
            except (json.JSONDecodeError, KeyError) as e:
                return {"error": f"Failed to parse JSON response: {str(e)}", "raw_response": result}
        else:
            return {"error": f"API request failed with status code {response.status_code}", "details": response.text}
    
    def detect_document_type(self, image):
        """Detect if the image is an invoice or a packing list"""
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Convert image to base64
        base64_image = self.encode_image(image)
        
        # Create payload for the API request
        payload = {
            "messages": [
                {
                    "role": "system", 
                    "content": "You are an AI specialized in document classification."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Determine if this document is an invoice or a packing list. Return only one word: either 'invoice' or 'packing_list'."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "model": self.model_name,
            "max_tokens": 50
        }
        
        # Make the API request
        api_endpoint = f"{self.base_url}openai/deployments/{self.model_name}/chat/completions?api-version={self.api_version}"
        response = requests.post(api_endpoint, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            doc_type = result["choices"][0]["message"]["content"].strip().lower()
            
            if doc_type == "invoice":
                return "invoice"
            elif doc_type == "packing_list":
                return "packing_list"
            else:
                return "unknown"
        else:
            return "unknown"
    
    def process_pdf(self, pdf_path, output_path=None):
        """Process PDF and extract information"""
        # Convert PDF to images
        images = self.pdf_to_images(pdf_path)
        results = []
        
        for i, image in enumerate(images):
            print(f"Processing page {i+1}/{len(images)}...")
            
            # Detect document type
            doc_type = self.detect_document_type(image)
            print(f"Detected document type: {doc_type}")
            
            # Process based on document type
            if doc_type == "invoice":
                result = self.analyze_invoice_image(image)
            elif doc_type == "packing_list":
                result = self.analyze_packing_list_image(image)
            else:
                # If unknown, try both
                invoice_result = self.analyze_invoice_image(image)
                if "error" not in invoice_result:
                    result = invoice_result
                else:
                    result = self.analyze_packing_list_image(image)
            
            results.append(result)
        
        # Save results to JSON file if output path is provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Results saved to {output_path}")
        
        return results

def main():
    parser = argparse.ArgumentParser(description='Process invoices and packing lists from PDF files.')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--output', '-o', help='Path to save the output JSON file')
    args = parser.parse_args()
    
    processor = InvoiceProcessor()
    
    # If no output path is provided, use the PDF filename with .json extension
    if not args.output:
        output_path = os.path.splitext(args.pdf_path)[0] + '_results.json'
    else:
        output_path = args.output
    
    results = processor.process_pdf(args.pdf_path, output_path)
    
    # Print summary
    for i, result in enumerate(results):
        if 'error' in result:
            print(f"Page {i+1}: Error - {result['error']}")
        else:
            print(f"Page {i+1}: Successfully extracted {result['type']} data")

if __name__ == "__main__":
    main()
