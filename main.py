import os
import glob
import tempfile
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from file_processor import read_transcript_file, validate_file_type, save_uploaded_file, extract_transcript_text,transcribe_audio_file
from field_extractor import FieldExtractor
from qa_evaluator import QAEvaluator
from database import Database

class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = JSONResponse(
                content={},
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
                    "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, ngrok-skip-browser-warning",
                    "Access-Control-Max-Age": "86400",
                }
            )
            return response
        
        # Process the request
        response = await call_next(request)
        
        # Add CORS headers to all responses
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, ngrok-skip-browser-warning"
        
        return response

app = FastAPI(title="Transcript Field Extractor", version="1.0.0")

# Add custom CORS middleware first (most important)
app.add_middleware(CustomCORSMiddleware)

# Enable CORS for frontend - Allow all origins (backup)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Allow credentials
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "ngrok-skip-browser-warning",
    ],
    expose_headers=["*"],
)

# Initialize components
field_extractor = FieldExtractor()
qa_evaluator = QAEvaluator()
database = Database()

# Mount static files if directory exists
static_dir = "static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return {"message": "Transcript Field Extractor API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

async def process_single_file(file: UploadFile):
    """Process a single file asynchronously and return results."""
    try:
        # Validate file type
        if not validate_file_type(file.filename):
            return {
                "success": False,
                "filename": file.filename,
                "error": "Please upload a valid audio file"
            }

        temp_dir = tempfile.mkdtemp(file.filename)
        tmp_audio_path = os.path.join(temp_dir, file.filename)
        
        # Read file content
        content = await file.read()
        with open(tmp_audio_path, "wb") as f:
            f.write(content)
        
        print(f"Processing: {tmp_audio_path}")
        
        # Transcribe audio file
        transcribed_audio = transcribe_audio_file(file_path=tmp_audio_path)
        transcript_text = extract_transcript_text(transcribed_audio, file.filename)

        # 1. Extract fields using Gemini
        extracted_fields = field_extractor.extract_fields_from_transcript(transcript_text)

        # 2. Save transcript to database
        transcript_id = database.save_transcript_data(
            filename=file.filename,
            original_text=transcript_text,
            extracted_fields=extracted_fields
        )

        # 3. Perform QA evaluation
        qa_evaluation = qa_evaluator.evaluate_transcript_qa(transcript_text)

        # 4. Save QA evaluation to database
        qa_evaluation_dict = qa_evaluation.dict()
        qa_id = database.save_qa_evaluation(transcript_id, qa_evaluation_dict)

        # Clean up temporary file
        try:
            os.remove(tmp_audio_path)
            os.rmdir(temp_dir)
        except:
            pass

        return {
            "success": True,
            "transcript_id": transcript_id,
            "qa_evaluation_id": qa_id,
            "filename": file.filename,
            "extracted_fields": extracted_fields,
            "qa_evaluation": qa_evaluation_dict,
            "total_score": qa_evaluation.total_score
        }

    except Exception as e:
        return {
            "success": False,
            "filename": file.filename,
            "error": str(e)
        }

@app.post("/upload-and-process")
async def upload_and_process(file: UploadFile = File(...)):
    """Process a single file upload."""
    result = await process_single_file(file)
    
    if result["success"]:
        return JSONResponse(content=result)
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.post("/bulk-upload-and-process")
async def bulk_upload_and_process(files: list[UploadFile] = File(..., alias="files")):
    """Process multiple files in bulk asynchronously with retry mechanism for failed files."""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Process files concurrently (but limit to avoid overwhelming the system)
        semaphore = asyncio.Semaphore(3)  # Process max 3 files at a time
        
        async def process_with_semaphore(file):
            async with semaphore:
                return await process_single_file(file)
        
        # First pass: Process all files
        tasks = [process_with_semaphore(file) for file in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results from first pass
        successful = []
        failed_files = []  # Store failed files for retry
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_files.append(files[i])
                failed_results.append({
                    "filename": files[i].filename,
                    "error": str(result),
                    "attempt": 1
                })
            elif result["success"]:
                successful.append(result)
            else:
                failed_files.append(files[i])
                failed_results.append({
                    **result,
                    "attempt": 1
                })
        
        # Second pass: Retry failed files
        if failed_files:
            print(f"Retrying {len(failed_files)} failed files...")
            
            # Retry failed files
            retry_tasks = [process_with_semaphore(file) for file in failed_files]
            retry_results = await asyncio.gather(*retry_tasks, return_exceptions=True)
            
            # Process retry results
            for i, result in enumerate(retry_results):
                if isinstance(result, Exception):
                    # File failed again, keep in failed list
                    failed_results[i]["error"] = f"Retry failed: {str(result)}"
                    failed_results[i]["attempt"] = 2
                elif result["success"]:
                    # File succeeded on retry, move to successful
                    successful.append(result)
                    failed_results[i] = None  # Mark for removal
                else:
                    # File failed again with different error
                    failed_results[i]["error"] = f"Retry failed: {result['error']}"
                    failed_results[i]["attempt"] = 2
            
            # Remove successful retries from failed list
            failed_results = [f for f in failed_results if f is not None]
        
        # Final results
        final_failed = failed_results
        final_successful = successful
        
        return JSONResponse(content={
            "success": True,
            "total_files": len(files),
            "successful_count": len(final_successful),
            "failed_count": len(final_failed),
            "successful_files": final_successful,
            "failed_files": final_failed,
            "message": f"Processing completed for {len(files)} files. {len(final_successful)} completed successfully, {len(final_failed)} failed after retry."
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/transcripts")
async def get_all_transcripts():
    try:
        transcripts = database.get_all_transcripts()
        return JSONResponse(
            content={
                "success": True,
                "transcripts": transcripts
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
                "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/transcripts/{transcript_id}")
async def get_transcript(transcript_id: int):
    try:
        transcript = database.get_transcript_by_id(transcript_id)
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")

        return JSONResponse(content={
            "success": True,
            "transcript": transcript
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle all preflight requests"""
    return JSONResponse(
        content={}, 
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, ngrok-skip-browser-warning",
            "Access-Control-Max-Age": "86400",
        }
    )

@app.options("/dashboard")
async def options_dashboard():
    """Handle preflight requests for dashboard endpoint"""
    return JSONResponse(
        content={}, 
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, ngrok-skip-browser-warning",
            "Access-Control-Max-Age": "86400",
        }
    )

@app.options("/bulk-upload-and-process")
async def options_bulk_upload():
    """Handle preflight requests for bulk upload endpoint"""
    return JSONResponse(
        content={}, 
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, ngrok-skip-browser-warning",
            "Access-Control-Max-Age": "86400",
        }
    )

@app.get("/dashboard")
async def get_dashboard():
    try:
        # Get all transcripts with their QA evaluations
        qa_evaluations = database.get_all_qa_evaluations()

        # Get summary statistics
        total_calls = len(qa_evaluations)
        if total_calls > 0:
            scores = [eval_data['total_score'] for eval_data in qa_evaluations]
            avg_score = sum(scores) / total_calls
            max_score = max(scores)
            min_score = min(scores)
        else:
            avg_score = max_score = min_score = 0

        return JSONResponse(
            content={
                "success": True,
                "dashboard_data": {
                    "total_calls": total_calls,
                    "average_score": round(avg_score, 1),
                    "highest_score": max_score,
                    "lowest_score": min_score,
                    "call_evaluations": qa_evaluations
                }
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
                "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/call-details/{transcript_id}")
async def get_call_details(transcript_id: int):
    try:
        # Get transcript data
        transcript = database.get_transcript_by_id(transcript_id)
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")

        # Get QA evaluation data
        qa_evaluation = database.get_qa_evaluation_by_transcript_id(transcript_id)

        return JSONResponse(content={
            "success": True,
            "call_data": {
                "transcript": transcript,
                "qa_evaluation": qa_evaluation
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/qa-evaluation/{qa_id}")
async def get_qa_evaluation(qa_id: int):
    try:
        qa_evaluation = database.get_qa_evaluation_by_id(qa_id)
        if not qa_evaluation:
            raise HTTPException(status_code=404, detail="QA evaluation not found")

        return JSONResponse(content={
            "success": True,
            "qa_evaluation": qa_evaluation
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add batch processing endpoint
@app.post("/process-directory")
async def process_directory():
    """Process all transcript files from the specified directory."""
    transcripts_dir = "/mnt/c/Users/User/Downloads/tanscripts"

    try:
        if not os.path.exists(transcripts_dir):
            raise HTTPException(status_code=404, detail="Transcripts directory not found")

        # Get all JSON files from the directory
        json_files = glob.glob(os.path.join(transcripts_dir, "*.json"))
        txt_files = glob.glob(os.path.join(transcripts_dir, "*.txt"))
        all_files = json_files + txt_files

        if not all_files:
            raise HTTPException(status_code=404, detail="No transcript files found in directory")

        processed_files = []
        failed_files = []

        for file_path in all_files:
            try:
                filename = os.path.basename(file_path)

                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()

                # Extract transcript text
                transcript_text = extract_transcript_text(file_content, filename)

                # 1. Extract fields using Gemini
                extracted_fields = field_extractor.extract_fields_from_transcript(transcript_text)

                # 2. Save transcript to database
                transcript_id = database.save_transcript_data(
                    filename=filename,
                    original_text=transcript_text,
                    extracted_fields=extracted_fields
                )

                # 3. Perform QA evaluation
                qa_evaluation = qa_evaluator.evaluate_transcript_qa(transcript_text)

                # 4. Save QA evaluation to database
                qa_evaluation_dict = qa_evaluation.dict()
                qa_id = database.save_qa_evaluation(transcript_id, qa_evaluation_dict)

                processed_files.append({
                    "filename": filename,
                    "transcript_id": transcript_id,
                    "qa_evaluation_id": qa_id,
                    "total_score": qa_evaluation.total_score
                })

            except Exception as e:
                failed_files.append({
                    "filename": os.path.basename(file_path),
                    "error": str(e)
                })

        return JSONResponse(content={
            "success": True,
            "total_files": len(all_files),
            "processed_successfully": len(processed_files),
            "failed": len(failed_files),
            "processed_files": processed_files,
            "failed_files": failed_files
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Catch-all route for missing resources
@app.get("/{path:path}")
async def catch_all(path: str):
    """Catch-all route to handle missing resources gracefully"""
    return JSONResponse(
        content={"error": f"Resource not found: /{path}"}, 
        status_code=404,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers",
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
