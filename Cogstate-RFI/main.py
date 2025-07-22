from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from rfiprocessor.core.agents.rfi_parser import RfiParserAgent
import uvicorn

app = FastAPI()

@app.post("/parse-rfi/")
def parse_rfi(
    file: UploadFile = File(None),
    markdown_text: str = Form(None)
):
    """
    Accepts a markdown file upload or raw markdown text, parses it using RfiParserAgent, and returns the result as JSON.
    """
    if not file and not markdown_text:
        raise HTTPException(status_code=400, detail="Either a file or markdown_text must be provided.")

    if file:
        content = file.file.read().decode("utf-8")
    else:
        content = markdown_text

    # Debug logging: print the markdown content being parsed
    print("\n--- MARKDOWN CONTENT BEING PARSED ---\n")
    print(content)
    print("\n--- END OF MARKDOWN CONTENT ---\n")

    try:
        parser = RfiParserAgent()
        result = parser.parse(content)
        # Return all extracted Q&A pairs, no filtering
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 