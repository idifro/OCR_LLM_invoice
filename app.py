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
MODEL_BASE_URL = os.getenv("MODEL_BASE_URL")
API_VERSION = os.getenv("API_VERSION")
MODEL_NAME = os.getenv("MODEL_NAME")
API_KEY = os.getenv("API_KEY")

# ASN API Configuration
ASN_API_URL = os.getenv("ASN_API_URL", "https://asn.mazedemo.in/api/method/asn_web.purchaseinvoiceandpacking.split_and_create_docs")
ASN_API_TOKEN = os.getenv("ASN_API_TOKEN", "d8b9d365596cfa3:05844281d60f0e0")

# Temp folder configuration
TEMP_OUTPUT_FOLDER = os.getenv("TEMP_OUTPUT_FOLDER", tempfile.gettempdir())

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
                    output_folder=TEMP_OUTPUT_FOLDER,
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
                content = result['choices'][0]['message']['content']
                # Parse the JSON
                data = json.loads(content)
                # Add document type
                data['type'] = 'invoice'
                return data
            except Exception as e:
                print(f"Error parsing invoice result: {e}")
                return {"error": f"Failed to parse invoice result: {str(e)}", "type": "invoice"}
        else:
            print(f"API request failed: {response.status_code}, {response.text}")
            return {"error": f"API request failed: {response.status_code}", "type": "invoice"}
    
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
    
    def send_to_asn_api(self, results):
        """Send extracted data to ASN API endpoint"""
        api_url = ASN_API_URL
        headers = {
            "Authorization": f"Token {ASN_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            # Filter out results with errors
            valid_results = [result for result in results if 'error' not in result]
            
            # Make the API request
            response = requests.post(api_url, headers=headers, json=valid_results)
            
            if response.status_code in [200, 201]:
                print("Successfully sent data to ASN API")
                return {
                    "success": True,
                    "response": response.json()
                }
            else:
                print(f"Failed to send data to ASN API. Status code: {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "details": response.text
                }
        except Exception as e:
            print(f"Error sending data to ASN API: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_multipage_invoice(self, images):
        """Process a multipage invoice PDF by analyzing each page and combining the results"""
        page_count = len(images)
        print(f"Processing multipage invoice with {page_count} pages...")
        
        # Initialize combined result structure
        combined_result = {
            "type": "multipage_invoice",
            "page_count": page_count,
            "vendor_name": "",
            "vendor_address": "",
            "delivery_address": "",
            "invoice_no": "",
            "date": "",
            "items": [],
            "totals": {
                "total_amount": "",
                "vat": "",
                "vat_amount": "",
                "discount": "",
                "net_price": ""
            },
            "processing_info": {
                "has_incomplete_item": False,
                "incomplete_description": ""
            }
        }
        
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Process first page to get header information
        first_image = images[0]
        base64_first_image = self.encode_image(first_image)
        
        # Extract header information from first page
        first_page_payload = {
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
                            "text": "Extract the following information from this invoice image and return it in a valid JSON format:\n\n1. Vendor Name\n2. Vendor Address\n3. Delivery Address\n4. Invoice No\n5. Date\n\nThe JSON should have keys: vendor_name, vendor_address, delivery_address, invoice_no, date."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_first_image}"
                            }
                        }
                    ]
                }
            ],
            "model": self.model_name,
            "max_tokens": 4000
        }
        
        # Make the API request for first page header info
        api_endpoint = f"{self.base_url}openai/deployments/{self.model_name}/chat/completions?api-version={self.api_version}"
        first_page_response = requests.post(api_endpoint, headers=headers, json=first_page_payload)
        
        if first_page_response.status_code == 200:
            result = first_page_response.json()
            try:
                # Extract the content
                content = result['choices'][0]['message']['content']
                # Parse the JSON
                header_data = json.loads(content)
                
                # Update combined result with header information
                combined_result["vendor_name"] = header_data.get("vendor_name", "")
                combined_result["vendor_address"] = header_data.get("vendor_address", "")
                combined_result["delivery_address"] = header_data.get("delivery_address", "")
                combined_result["invoice_no"] = header_data.get("invoice_no", "")
                combined_result["date"] = header_data.get("date", "")
                
            except Exception as e:
                print(f"Error parsing first page header: {e}")
        else:
            print(f"API request failed for first page: {first_page_response.status_code}")
        
        # Process all pages for table items
        for i, image in enumerate(images):
            print(f"Processing page {i+1}/{page_count} table items...")
            base64_image = self.encode_image(image)
            
            # Extract table items from this page
            table_payload = {
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are an AI specialized in extracting structured information from complex invoice tables with multiline items. You must ALWAYS return a valid, parseable JSON object without any additional text, explanation or markdown formatting."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Extract the table items from this invoice image (page {i+1} of {page_count}) and return ONLY a valid JSON object without any additional text.\n\nIMPORTANT NOTES ABOUT THE TABLE STRUCTURE AND DESCRIPTION FIELD:\n1. Each line item has TWO codes: an alphanumeric code AND a numeric code. Capture both in the 'code' field separated by a space or comma.\n\n2. DESCRIPTION FIELD PARSING RULES (CRITICAL):\n   - Description typically starts with text and ends with 'INTRASTAT' followed by a number\n   - If a line starts with 'INTRASTAT' followed by a number, it belongs to the PREVIOUS line item\n   - The INTRASTAT number serves as an end-of-line delimiter for descriptions\n   - If the last item on the page has no INTRASTAT number, it means the description continues on the next page\n   - Split each description into two separate fields: 'description' (the main text) and 'intrastat_number' (just the number)\n\n3. For each row in the table extract:\n   - Code (include both alphanumeric and numeric codes)\n   - Description (all text EXCEPT the INTRASTAT part)\n   - Intrastat_number (just the number following 'INTRASTAT')\n   - PCS (pieces)\n   - Quantity\n   - Unit Price\n   - Discount\n   - Net Price EURO\n\n4. Also extract any information about page continuity (e.g., 'continued on next page').\n\nReturn ONLY a JSON object with EXACTLY this structure:\n{{\n  \"items\": [\n    {{\n      \"code\": \"string\",\n      \"description\": \"string\",\n      \"intrastat_number\": \"string\",\n      \"pcs\": \"string\",\n      \"quantity\": \"string\",\n      \"unit_price\": \"string\",\n      \"discount\": \"string\",\n      \"net_price\": \"string\"\n    }}\n  ],\n  \"has_more_pages\": boolean,\n  \"has_incomplete_item\": boolean\n}}\n\nIf the last item has an incomplete description (missing INTRASTAT), set has_incomplete_item to true.\n\nEnsure your JSON is valid and can be parsed by standard JSON parsers."
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
                "max_tokens": 8000
            }
            
            # Make the API request for table items
            table_response = requests.post(api_endpoint, headers=headers, json=table_payload)
            

            if table_response.status_code == 200:
                result = table_response.json()
                try:
                    # Extract the content
                    content = result['choices'][0]['message']['content']
                    print(f"\nRaw JSON content from page {i+1}:\n{content}\n")
                    
                    # Try to fix common JSON formatting issues
                    content = content.strip()
                    # Remove any markdown code block indicators
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.startswith('```'):
                        content = content[3:]
                    if content.endswith('```'):
                        content = content[:-3]
                    content = content.strip()
                    
                    # Parse the JSON with detailed error handling
                    try:
                        table_data = json.loads(content)
                    except json.JSONDecodeError as json_err:
                        print(f"JSON parsing error on page {i+1}: {json_err}")
                        print(f"Problematic content: {content[:100]}...")
                        print(f"Attempting to fix common JSON issues...")
                        
                        # More aggressive fixes
                        import re
                        # Try to extract valid JSON if embedded in other text
                        json_pattern = r'\{[^\{\}]*\"items\"[^\{\}]*\}'
                        match = re.search(json_pattern, content)
                        if match:
                            possible_json = match.group(0)
                            try:
                                table_data = json.loads(possible_json)
                                print(f"Successfully extracted and parsed embedded JSON")
                            except:
                                # Last resort - create empty structure
                                print(f"Could not fix JSON, using empty structure")
                                table_data = {"items": [], "has_more_pages": False}
                        else:
                            # Last resort - create empty structure
                            print(f"Could not fix JSON, using empty structure")
                            table_data = {"items": [], "has_more_pages": False}
                    
                    # Process items from this page
                    if "items" in table_data and isinstance(table_data["items"], list):
                        print(f"Found {len(table_data['items'])} items on page {i+1}")
                        
                        # Check if there was an incomplete item from previous page
                        if i > 0 and combined_result["processing_info"]["has_incomplete_item"] and len(table_data["items"]) > 0:
                            print(f"Handling incomplete item from previous page")
                            # Get the first item from this page to see if it starts with INTRASTAT
                            first_item = table_data["items"][0]
                            
                            # Check if this item has an INTRASTAT number that belongs to previous item
                            if first_item.get("description", "").strip().startswith("INTRASTAT") or \
                               "intrastat_number" in first_item and first_item["intrastat_number"]:
                                
                                # Get the last item from previous page
                                if combined_result["items"]:
                                    last_item = combined_result["items"][-1]
                                    
                                    # Update the last item's INTRASTAT number
                                    if "intrastat_number" in first_item:
                                        last_item["intrastat_number"] = first_item["intrastat_number"]
                                    else:
                                        # Extract INTRASTAT from description
                                        intrastat_text = first_item.get("description", "")
                                        last_item["intrastat_number"] = intrastat_text.replace("INTRASTAT", "").strip()
                                    
                                    # Remove the first item as it's been merged
                                    table_data["items"] = table_data["items"][1:]
                                    print(f"Merged INTRASTAT number to previous page item")
                                
                            # If first item is a continuation of description
                            elif combined_result["processing_info"]["incomplete_description"]:
                                if combined_result["items"]:
                                    # Append the description to the previous item
                                    last_item = combined_result["items"][-1]
                                    continuation_text = combined_result["processing_info"]["incomplete_description"]
                                    
                                    if "description" in first_item:
                                        last_item["description"] = continuation_text + " " + first_item["description"]
                                    
                                    # If this item now has an INTRASTAT, update it
                                    if "intrastat_number" in first_item:
                                        last_item["intrastat_number"] = first_item["intrastat_number"]
                                    
                                    # Remove the first item as it's been merged
                                    table_data["items"] = table_data["items"][1:]
                                    print(f"Merged continued description to previous page item")
                            
                            # Reset the incomplete flag
                            combined_result["processing_info"]["has_incomplete_item"] = False
                            combined_result["processing_info"]["incomplete_description"] = ""
                        
                        # Add the items from this page
                        combined_result["items"].extend(table_data["items"])
                        
                        # Check if this page has an incomplete item at the end
                        if "has_incomplete_item" in table_data and table_data["has_incomplete_item"]:
                            combined_result["processing_info"]["has_incomplete_item"] = True
                            # If the last item has no INTRASTAT, mark its description for continuation
                            if combined_result["items"] and not combined_result["items"][-1].get("intrastat_number"):
                                combined_result["processing_info"]["incomplete_description"] = combined_result["items"][-1].get("description", "")
                                print(f"Marked item for continuation on next page")
                        else:
                            combined_result["processing_info"]["has_incomplete_item"] = False
                            combined_result["processing_info"]["incomplete_description"] = ""
                    
                except Exception as e:
                    print(f"Error processing table items on page {i+1}: {str(e)}")
                    # Fallback to empty structure
                    print(f"Using empty structure due to error")
            else:
                print(f"API request failed for page {i+1} table: {table_response.status_code}")
            
            # On last page, extract totals
            if i == page_count - 1:
                totals_payload = {
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are an AI specialized in extracting structured information from invoice totals. Extract information in a structured JSON format without any explanations."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Extract the following total information from this final invoice page and return it in a valid JSON format:\n\n1. Total Amount\n2. VAT Rate\n3. VAT Amount\n4. Discount\n5. Net Price\n\nThe JSON should have keys: total_amount, vat, vat_amount, discount, net_price."
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
                
                # Make the API request for totals
                totals_response = requests.post(api_endpoint, headers=headers, json=totals_payload)
                
                if totals_response.status_code == 200:
                    result = totals_response.json()
                    try:
                        # Extract the content
                        content = result['choices'][0]['message']['content']
                        # Parse the JSON
                        totals_data = json.loads(content)
                        
                        # Update combined result with totals
                        combined_result["totals"]["total_amount"] = totals_data.get("total_amount", "")
                        combined_result["totals"]["vat"] = totals_data.get("vat", "")
                        combined_result["totals"]["vat_amount"] = totals_data.get("vat_amount", "")
                        combined_result["totals"]["discount"] = totals_data.get("discount", "")
                        combined_result["totals"]["net_price"] = totals_data.get("net_price", "")
                        
                    except Exception as e:
                        print(f"Error parsing totals: {e}")
                else:
                    print(f"API request failed for totals: {totals_response.status_code}")
                    
        return combined_result

    def process_pdf(self, pdf_path, output_path=None, send_to_api=True):
        """Process PDF and extract information"""
        # Convert PDF to images
        images = self.pdf_to_images(pdf_path)
        page_count = len(images)
        print(f"PDF has {page_count} pages")
        
        # For multipage PDFs, check if all pages are invoices
        if page_count > 1:
            print("Checking document types for all pages...")
            
            # Check each page's document type
            page_types = []
            all_invoice = True
            
            for i, image in enumerate(images):
                doc_type = self.detect_document_type(image)
                page_types.append(doc_type)
                print(f"Page {i+1}: Detected document type: {doc_type}")
                if doc_type != "invoice":
                    all_invoice = False
            
            # If all pages are invoices, process as multipage invoice
            if all_invoice:
                print("All pages are invoices, processing as multipage invoice")
                combined_result = self.analyze_multipage_invoice(images)
                results = [combined_result]  # Wrap in a list to maintain compatibility with existing code
            else:
                # Fall back to standard processing if not all pages are invoices
                print("Mixed document types detected, processing standard way")
                print(f"Page types detected: {page_types}")
                results = self.process_standard_pdf(images)
        else:
            # Single page - use standard processing
            print("Single page document detected, processing standard way")
            results = self.process_standard_pdf(images)
        
        # Save results to JSON file if output path is provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Results saved to {output_path}")
        
        # Send data to ASN API if requested
        api_response = None
        if send_to_api:
            api_response = self.send_to_asn_api(results)
            print("API Response:", json.dumps(api_response, indent=2))
        
        return results, api_response
        
    def process_standard_pdf(self, images):
        """Process PDF using the standard method (page by page)"""
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
            
        return results

def main():
    parser = argparse.ArgumentParser(description='Process invoices and packing lists from PDF files.')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--output', '-o', help='Path to save the output JSON file')
    parser.add_argument('--no-api', action='store_true', help='Skip sending data to ASN API')
    args = parser.parse_args()
    
    processor = InvoiceProcessor()
    
    # If no output path is provided, use the PDF filename with .json extension
    if not args.output:
        output_path = os.path.splitext(args.pdf_path)[0] + '_results.json'
    else:
        output_path = args.output
    
    # Process PDF and optionally send to API
    results, api_response = processor.process_pdf(args.pdf_path, output_path, send_to_api=not args.no_api)
    
    # Print summary
    for i, result in enumerate(results):
        if 'error' in result:
            print(f"Page {i+1}: Error - {result['error']}")
        else:
            print(f"Page {i+1}: Successfully extracted {result['type']} data")
    
    # Print API response summary if data was sent to API
    if not args.no_api:
        if api_response and api_response.get('success'):
            print("\nSuccessfully sent data to ASN API")
        else:
            print("\nFailed to send data to ASN API. See log for details.")

if __name__ == "__main__":
    main()
