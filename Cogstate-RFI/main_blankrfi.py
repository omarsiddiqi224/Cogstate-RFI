from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from rfiprocessor.core.agents.blank_rfi_parser import BlankRfiParserAgent
from config.config import Config
import os
import tempfile
import uvicorn

app = FastAPI()

@app.post("/parse-blank-rfi/")
def parse_blank_rfi(
    file: UploadFile = File(None),
    markdown_text: str = Form(None)
):
    """
    Accepts a markdown file upload or raw markdown text, parses it using BlankRfiParserAgent (tries OpenAI first, falls back to Gemini Pro LLM if OpenAI fails), and returns the result as JSON.
    Handles binary files (PDF, DOCX, XLSX, etc.) by converting them to markdown first.
    """
    if not file and not markdown_text:
        raise HTTPException(status_code=400, detail="Either a file or markdown_text must be provided.")

    if file:
        # Save the uploaded file to a temporary location
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name
        # Convert to markdown using your converter
        from rfiprocessor.services.markdown_converter import MarkdownConverter, ProcessorType
        converter = MarkdownConverter()
        ext = suffix.lower()
        processor = ProcessorType.UNSTRUCTURED if ext in [".xls", ".xlsx", ".doc", ".docm"] else ProcessorType.MARKITDOWN
        markdown_content, _ = converter.convert_to_markdown(tmp_path, processor=processor)
        content = markdown_content
        os.unlink(tmp_path)  # Clean up temp file
    else:
        content = markdown_text

    # Debug logging: print the markdown content being parsed
    print("\n--- MARKDOWN CONTENT BEING PARSED ---\n")
    print(content)
    print("\n--- END OF MARKDOWN CONTENT ---\n")

    try:
        # Try OpenAI first, fallback to Gemini Pro on any error
        try:
            parser = BlankRfiParserAgent()  # Use default (OpenAI)
            result = parser.parse(content)
        except Exception as openai_exc:
            print("OpenAI failed, falling back to Gemini:", openai_exc)
            gemini_llm = Config.get_gemini_pro_llm()
            parser = BlankRfiParserAgent(llm=gemini_llm)
            result = parser.parse(content)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main_blankrfi:app", host="0.0.0.0", port=8001, reload=True) 