import sys
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from json_processing import process_json_files, get_current_object, set_user_decision, get_current_filename, get_processed_status
from ui_status import progress
import threading
import logging
from pydantic import BaseModel

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Set up logging to both file and console
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('logs/fastapi_app.log'),
                        logging.StreamHandler(sys.stdout)
                    ])

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

processing_thread = None

# Define global input and output directories
INPUT_DIR = '../04_relevant_analysis_results'
OUTPUT_DIR = '../06_relevant_analysis_final_results'

class Decision(BaseModel):
    decision: int | bool | str  # Allow multiple types for decision

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logging.error(f"Error rendering index: {str(e)}")
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@app.get("/start_processing")
async def start_processing():
    global processing_thread
    if processing_thread is None or not processing_thread.is_alive():
        processing_thread = threading.Thread(target=process_json_files, args=(INPUT_DIR, OUTPUT_DIR))
        processing_thread.start()
        return {"status": "Processing started"}
    else:
        return {"status": "Processing already in progress"}

@app.get("/stop_processing")
async def stop_processing():
    global processing_thread
    if processing_thread and processing_thread.is_alive():
        # Implement a way to stop the processing thread safely
        return {"status": "Processing stopped"}
    else:
        return {"status": "No processing in progress"}

@app.get("/progress")
async def get_progress():
    file_progress, total_progress = progress.get()
    return {"file_progress": file_progress, "total_progress": total_progress}

@app.get("/current_object")
async def current_object():
    if processing_thread is None or not processing_thread.is_alive():
        return None

    obj = get_current_object()
    logging.debug(f"Current object from get_current_object: {obj}")
    
    if obj:
        # Create a copy to avoid modifying the original
        response_obj = dict(obj)
        if 'current_filename' not in response_obj:
            response_obj['current_filename'] = get_current_filename()
        
        # Ensure code_id is properly included
        if 'code_id' in obj:
            logging.debug(f"code_id in object: {obj['code_id']}")
        else:
            logging.debug("code_id not found in object")
            
        # Log all fields for debugging
        logging.debug("Fields in response object:")
        for key, value in response_obj.items():
            logging.debug(f"  {key}: {value}")
        
        return response_obj
    else:
        logging.debug("No current object available")
        return None

@app.post("/submit_decision")
async def submit_decision(decision: Decision):
    try:
        logging.info(f"Received decision: {decision.decision}")
        # Convert the decision to the correct type
        if isinstance(decision.decision, str):
            if decision.decision.lower() == 'true':
                decision_value = True
            elif decision.decision.lower() == 'false':
                decision_value = False
            else:
                decision_value = int(decision.decision)
        else:
            decision_value = decision.decision
            
        logging.info(f"Converted decision value: {decision_value}")
        set_user_decision(decision_value)
        logging.info("Decision set successfully")
        return {"status": "Decision received"}
    except Exception as e:
        logging.error(f"Error submitting decision: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/processed_status")
async def processed_status():
    status = get_processed_status()
    return status

if __name__ == '__main__':
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8080)
    except Exception as e:
        logging.error(f"Error starting FastAPI app: {str(e)}")
