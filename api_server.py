import os
import tempfile
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app import InvoiceProcessor

app = FastAPI(
    title="Invoice OCR API",
    description="API for extracting data from invoice PDFs and sending to ASN API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/process-pdf/")
async def process_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file to extract invoice/packing list data and send to ASN API.
    """
    if not file.filename.lower().endswith('.pdf'):
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Only PDF files are supported"}
        )
    
    # Create a processor instance
    processor = InvoiceProcessor()
    
    try:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file_path = temp_file.name
            contents = await file.read()
            temp_file.write(contents)
        
        # Process the PDF
        results, api_response = processor.process_pdf(temp_file_path, send_to_api=True)
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        # Check if ASN API call was successful
        if api_response and api_response.get("success"):
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "PDF processed and data sent to ASN API successfully", 
                    "filename": file.filename,
                    "extracted_data": results,
                    "api_response": api_response
                }
            )
        else:
            error_detail = ""
            if api_response:
                error_detail = f": {api_response.get('error', '')} {api_response.get('details', '')}"
            
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Failed to send data to ASN API{error_detail}",
                    "filename": file.filename,
                    "extracted_data": results
                }
            )
    
    except Exception as e:
        # Clean up if an error occurs
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Error processing PDF: {str(e)}"
            }
        )

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"success": True, "message": "Invoice OCR API is running"}

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)