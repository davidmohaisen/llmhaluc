import json
import os
import re
from ui_status import update_progress
import logging
import time
import threading

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/processing.log'),
        logging.StreamHandler()
    ]
)

current_object = None
user_decision = None
current_filename = None
current_review_phase = None
current_show_analysis = False
current_conflict = False
current_auto_label = None
current_first_decision = None
processed_objects = []
processing_paused = threading.Event()

def get_current_object():
    global current_object, current_filename, current_review_phase, current_show_analysis, current_conflict
    if current_object is None:
        logging.debug("No current object available")
        return None

    response_obj = dict(current_object)
    if not current_show_analysis:
        response_obj['relevance_analysis'] = None

    response_obj['relevance_label'] = None

    response_obj['current_filename'] = current_filename
    response_obj['review_phase'] = current_review_phase
    response_obj['show_analysis'] = current_show_analysis
    response_obj['conflict'] = current_conflict
    logging.debug(f"Getting current object: {response_obj}")
    return response_obj

def get_current_filename():
    global current_filename
    logging.debug(f"Getting current filename: {current_filename}")
    return current_filename

def set_user_decision(decision):
    global user_decision, processing_paused
    logging.info(f"Setting user decision to: {decision} (phase {current_review_phase})")
    user_decision = decision
    processing_paused.set()  # Resume processing
    logging.info("User decision set successfully")

def clear_review_state():
    global current_object, current_filename, current_review_phase, current_show_analysis
    global current_conflict, current_auto_label, current_first_decision
    current_object = None
    current_filename = None
    current_review_phase = None
    current_show_analysis = False
    current_conflict = False
    current_auto_label = None
    current_first_decision = None

def get_processed_status():
    return [{"id": obj.get("id"), "sub_id": obj.get("sub_id")} for obj in processed_objects[-10:]]

def process_json_files(input_dir, output_dir):
    global current_object, user_decision, current_filename, processed_objects, processing_paused
    global current_review_phase, current_show_analysis, current_conflict
    global current_auto_label, current_first_decision
    
    logging.info(f"Starting to process JSON files from {input_dir}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    json_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.json')])
    total_files = len(json_files)
    logging.info(f"Found {total_files} JSON files to process")

    for file_index, filename in enumerate(json_files, 1):
        current_filename = filename
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        logging.info(f"Processing file {file_index}/{total_files}: {filename}")
        
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        total_objects = len(data)
        for obj_index, obj in enumerate(data, 1):
            logging.debug(f"Processing object {obj_index}/{total_objects} from file {filename}")
            current_filename = filename
            current_object = obj
            obj['relevance_label'] = None
            current_review_phase = 1
            current_show_analysis = False
            current_conflict = False
            current_auto_label = process_json_object(obj)
            current_first_decision = None

            logging.info(
                "Auto label extracted for object %s: %s",
                obj.get("id"),
                current_auto_label,
            )

            processing_paused.clear()  # Pause processing for first review
            logging.info(f"Waiting for first user decision on object ID: {obj.get('id')}")
            while not processing_paused.is_set():
                time.sleep(0.1)  # Wait for user decision

            current_first_decision = user_decision
            user_decision = None

            if current_auto_label is None:
                logging.info(
                    "Auto label unavailable; accepting first decision for object %s: %s",
                    obj.get("id"),
                    current_first_decision,
                )
                final_decision = current_first_decision
            elif current_first_decision == current_auto_label:
                logging.info(
                    "Decision matches auto label for object %s: %s",
                    obj.get("id"),
                    current_first_decision,
                )
                final_decision = current_first_decision
            else:
                logging.warning(
                    "Decision mismatch for object %s (auto=%s, user=%s). Triggering second review.",
                    obj.get("id"),
                    current_auto_label,
                    current_first_decision,
                )
                current_review_phase = 2
                current_show_analysis = True
                current_conflict = True

                processing_paused.clear()  # Pause processing for second review
                logging.info(f"Waiting for second user decision on object ID: {obj.get('id')}")
                while not processing_paused.is_set():
                    time.sleep(0.1)  # Wait for user decision

                final_decision = user_decision
                user_decision = None

                logging.info(
                    "Second decision received for object %s: %s",
                    obj.get("id"),
                    final_decision,
                )

            obj['relevance_label'] = final_decision
            processed_objects.append({"id": obj.get("id"), "sub_id": obj.get("sub_id")})
            logging.info(
                "Final relevance_label set for object %s: %s",
                obj.get("id"),
                obj['relevance_label'],
            )

            clear_review_state()
            
            update_progress(file_index, total_files, obj_index, total_objects)
            
            # Remove relevance_analysis field before writing to output
            obj.pop('relevance_analysis', None)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logging.info(f"Completed processing file {filename}")

def process_json_object(obj):
    logging.debug(f"Processing object with ID: {obj.get('id')}")
    logging.debug(f"Object code_id: {obj.get('code_id')}")
    result = extract_result(obj.get('relevance_analysis', ''))

    if result is not None:
        logging.info(f"Extracted auto label for object {obj.get('id')}: {result}")
    else:
        logging.info(f"No auto label extracted for object {obj.get('id')}")

    return result

def extract_result(text):
    if not text:
        logging.debug("Empty text provided for result extraction")
        return None
        
    # Replace all non-alphanumeric characters with spaces and convert to lowercase
    cleaned_text = re.sub(r'[^a-zA-Z0-9]', ' ', text).lower()
    # Replace multiple spaces with a single space
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    logging.debug(f"Cleaned text for analysis: {cleaned_text}")

    vulnerable_pattern = r'result vulnerable'
    not_vulnerable_pattern = r'result not vulnerable'
    not_relevant_pattern = r'result not relevant'
    
    vulnerable_matches = re.findall(vulnerable_pattern, cleaned_text)
    not_vulnerable_matches = re.findall(not_vulnerable_pattern, cleaned_text)
    not_relevant_matches = re.findall(not_relevant_pattern, cleaned_text)
    
    if len(vulnerable_matches) == 1 and len(not_vulnerable_matches) == 0 and len(not_relevant_matches) == 0:
        return 1  # Vulnerable
    elif len(not_vulnerable_matches) == 1 and len(vulnerable_matches) == 0 and len(not_relevant_matches) == 0:
        return 0  # Not vulnerable
    elif len(not_relevant_matches) == 1 and len(vulnerable_matches) == 0 and len(not_vulnerable_matches) == 0:
        return -1  # Not relevant
    else:
        return None  # Require user validation
