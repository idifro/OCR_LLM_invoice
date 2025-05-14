import requests
import os
import json
import argparse

def process_pdf(pdf_path, api_url="http://localhost:8000/process-pdf/"):
    """
    Send a PDF file to the OCR API server for processing
    
    Args:
        pdf_path: Path to the PDF file
        api_url: URL of the API endpoint
        
    Returns:
        dict: API response
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found - {pdf_path}")
        return {"success": False, "message": "File not found"}
    
    if not pdf_path.lower().endswith('.pdf'):
        print("Error: Only PDF files are supported")
        return {"success": False, "message": "Only PDF files are supported"}
    
    try:
        # Prepare the file for upload
        files = {"file": (os.path.basename(pdf_path), open(pdf_path, "rb"), "application/pdf")}
        
        # Make the API request
        print(f"Sending {pdf_path} to OCR API server...")
        response = requests.post(api_url, files=files)
        
        # Make sure the file is closed
        files["file"][1].close()
        
        # Process the response
        if response.status_code == 200:
            result = response.json()
            print("Success! PDF processed and data sent to ASN API")
            return result
        else:
            print(f"Error: API request failed with status code {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error message: {error_data.get('message', 'Unknown error')}")
                return error_data
            except:
                return {
                    "success": False, 
                    "message": f"API request failed with status code {response.status_code}",
                    "details": response.text
                }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"success": False, "message": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Send PDF to OCR API Server")
    parser.add_argument("pdf_path", help="Path to the PDF file to process")
    parser.add_argument("--api-url", default="http://localhost:8000/process-pdf/", 
                      help="URL of the OCR API endpoint")
    parser.add_argument("--output", "-o", help="Path to save the output JSON file")
    
    args = parser.parse_args()
    
    # Send the PDF to the API
    result = process_pdf(args.pdf_path, args.api_url)
    
    # Save output if requested
    if args.output and result:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {args.output}")
    
    # Print a summary
    if result and result.get("success"):
        print("\nSummary:")
        print(f"Filename: {result.get('filename', 'Unknown')}")
        
        # Print extracted data summary
        if "extracted_data" in result:
            for i, data in enumerate(result["extracted_data"]):
                if "error" in data:
                    print(f"  Page {i+1}: Error - {data['error']}")
                else:
                    print(f"  Page {i+1}: Successfully extracted {data['type']} data")

if __name__ == "__main__":
    main()