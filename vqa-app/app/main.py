# app/main.py

from fastapi import FastAPI, File, Form, UploadFile
from PIL import Image
from transformers import AutoModel, AutoTokenizer
import torch
from torch.cuda.amp import autocast
import os
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

# Define cache directory
CACHE_DIR = "/app/transformers_cache"

# Ensure the cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# Set environment variable to work in offline mode
os.environ["TRANSFORMERS_OFFLINE"] = "1"

@app.post("/inference/")
async def inference(file: UploadFile = File(...), context: str = Form(""), query: str = Form("Can you summarize this image?")):
    file_location = f"/app/{file.filename}"
    
    try:
        # Save the uploaded file
        with open(file_location, "wb") as f:
            contents = await file.read()
            f.write(contents)
        
        # Verify if the file is a valid image
        try:
            image = Image.open(file_location).convert('RGB')
        except Exception as e:
            return {"error": f"Cannot identify image file: {e}"}
        
        # Proceed with your image inference code
        
        if torch.cuda.is_available():
            logger.info(f"GPU detected. Proceeding with inference for image: {file_location}")
        else:
            logger.info(f"No GPU detected. Sorry cannot run inference for image: {file_location}")
            return ""

        input_prompt = f"{context}\nQuestion: {query}"
        msgs = [{'role': 'user', 'content': input_prompt}]
        response = ""
        try:
            model = AutoModel.from_pretrained('openbmb/MiniCPM-Llama3-V-2_5', cache_dir=CACHE_DIR, revision='e978c4c9b177e8d1f36deeec20edb18377dc2ff7', trust_remote_code=True, torch_dtype=torch.float16)
            model = model.to(device='cuda')
            tokenizer = AutoTokenizer.from_pretrained('openbmb/MiniCPM-Llama3-V-2_5', cache_dir=CACHE_DIR, revision='e978c4c9b177e8d1f36deeec20edb18377dc2ff7', trust_remote_code=True)
            model.eval()

            # Use autocast for mixed precision to save memory
            with autocast():
                response = model.chat(
                    image=image,
                    msgs=msgs,
                    tokenizer=tokenizer,
                    sampling=True,
                    temperature=0.7,
                    system_prompt="You are an expert in analysing openshift performance metrics",
                )

        except torch.cuda.OutOfMemoryError:
            print("CUDA out of memory. Clearing cache and retrying...")
            torch.cuda.empty_cache()
            return "error: CUDA out of memory"
            
        
        # Free up memory
        torch.cuda.empty_cache()

        return response

    finally:
        # Delete the file after processing
        if os.path.exists(file_location):
            os.remove(file_location)