from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from rfiprocessor.core.agents.enhanced_blank_rfi_agent import EnhancedBlankRfiAgent
from rfiprocessor.services.markdown_converter import MarkdownConverter, ProcessorType
import asyncio
import json
import os
import tempfile
import uvicorn
from typing import AsyncGenerator

app = FastAPI(title="Enhanced Blank RFI Processor", version="2.0.0")

# Global agent instance
enhanced_agent = None

@app.on_event("startup")
async def startup_event():
    global enhanced_agent
    enhanced_agent = EnhancedBlankRfiAgent()

@app.post("/process-blank-rfi/batch")
async def process_blank_rfi_batch(
    file: UploadFile = File(None),
    markdown_text: str = Form(None)
):
    """
    Process entire blank RFI document and return all answers at once.
    """
    if not file and not markdown_text:
        raise HTTPException(status_code=400, detail="Either a file or markdown_text must be provided.")

    try:
        # Get markdown content
        if file:
            markdown_content = await _convert_file_to_markdown(file)
        else:
            markdown_content = markdown_text

        # Process document
        result = await enhanced_agent.process_document(markdown_content, processing_mode="batch")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-blank-rfi/question")
async def process_single_question(question: str = Form(...)):
    """
    Process a single question and return answer with attribution.
    """
    try:
        result = await enhanced_agent.process_single_question(question)
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-blank-rfi/stream")
async def process_blank_rfi_stream(
    file: UploadFile = File(None),
    markdown_text: str = Form(None)
):
    """
    Process blank RFI document with streaming progress updates.
    """
    if not file and not markdown_text:
        raise HTTPException(status_code=400, detail="Either a file or markdown_text must be provided.")

    try:
        # Get markdown content
        if file:
            markdown_content = await _convert_file_to_markdown(file)
        else:
            markdown_content = markdown_text

        async def generate_stream():
            try:
                # First, try to parse the document with timeout protection
                yield f"data: {json.dumps({'status': 'parsing', 'message': 'Parsing document...'})}\n\n"
                
                # Parse the document
                parsed_data = await asyncio.wait_for(
                    asyncio.to_thread(enhanced_agent.blank_rfi_parser.parse, markdown_content),
                    timeout=300  # 5 minutes total timeout
                )
                
                # Extract questions properly
                question_objects = parsed_data.get("questions", [])
                questions = []
                for q in question_objects:
                    if isinstance(q, dict) and "question" in q:
                        questions.append(q["question"])
                    elif isinstance(q, str):
                        questions.append(q)
                    else:
                        questions.append(str(q))
                
                if not questions:
                    yield f"data: {json.dumps({'status': 'completed', 'total_questions': 0, 'results': [], 'message': 'No questions found in document'})}\n\n"
                    return
                
                yield f"data: {json.dumps({'status': 'questions_extracted', 'total_questions': len(questions)})}\n\n"
                
                # Process questions incrementally
                results = []
                for i, question in enumerate(questions):
                    try:
                        yield f"data: {json.dumps({'status': 'processing', 'progress': {'current': i+1, 'total': len(questions), 'percentage': ((i+1)/len(questions))*100}, 'current_question': question})}\n\n"
                        
                        result = await asyncio.wait_for(
                            enhanced_agent._process_question_with_variants(question),
                            timeout=120  # 2 minutes per question
                        )
                        
                        formatted_result = {
                            "question": question,
                            "answer": result["answer"],
                            "confidence_score": result["confidence_score"],
                            "sources": result["sources"],
                            "processing_metadata": result["metadata"]
                        }
                        results.append(formatted_result)
                        
                        # Send progress update with current result
                        yield f"data: {json.dumps({'status': 'processing', 'progress': {'current': i+1, 'total': len(questions), 'percentage': ((i+1)/len(questions))*100}, 'current_result': formatted_result})}\n\n"
                        
                    except asyncio.TimeoutError:
                        error_result = {
                            "question": question,
                            "answer": "Processing timed out for this question",
                            "confidence_score": 0.0,
                            "sources": [],
                            "error": "timeout"
                        }
                        results.append(error_result)
                        yield f"data: {json.dumps({'status': 'processing', 'progress': {'current': i+1, 'total': len(questions), 'percentage': ((i+1)/len(questions))*100}, 'current_result': error_result, 'warning': 'Question processing timed out'})}\n\n"
                        
                    except Exception as e:
                        error_result = {
                            "question": question,
                            "answer": f"Error processing question: {str(e)}",
                            "confidence_score": 0.0,
                            "sources": [],
                            "error": str(e)
                        }
                        results.append(error_result)
                        yield f"data: {json.dumps({'status': 'processing', 'progress': {'current': i+1, 'total': len(questions), 'percentage': ((i+1)/len(questions))*100}, 'current_result': error_result, 'warning': f'Question processing failed: {str(e)}'})}\n\n"
                
                # Final result
                final_result = {
                    "status": "completed",
                    "total_questions": len(questions),
                    "results": results,
                    "metadata": parsed_data.get("meta_data", {}),
                    "processing_summary": {
                        "successful": len([r for r in results if "error" not in r]),
                        "failed": len([r for r in results if "error" in r]),
                        "chunked_processing": parsed_data.get("processing_info", {}).get("chunked_processing", False)
                    }
                }
                yield f"data: {json.dumps(final_result)}\n\n"
                
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'status': 'error', 'error': 'Document processing timed out. Document may be too large or complex.'})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'status': 'error', 'error': f'Processing failed: {str(e)}'})}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _convert_file_to_markdown(file: UploadFile) -> str:
    """Convert uploaded file to markdown."""
    suffix = os.path.splitext(file.filename)[1]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        converter = MarkdownConverter()
        ext = suffix.lower()
        processor = ProcessorType.UNSTRUCTURED if ext in [".xls", ".xlsx", ".doc", ".docm"] else ProcessorType.MARKITDOWN
        markdown_content, _ = converter.convert_to_markdown(tmp_path, processor=processor)
        return markdown_content
    finally:
        os.unlink(tmp_path)

if __name__ == "__main__":
    uvicorn.run("main_enhanced_blank_rfi:app", host="0.0.0.0", port=8002, reload=True)