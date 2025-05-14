from fastapi import FastAPI, File, Form, UploadFile
from typing import List
from PIL import Image
from transformers import MllamaForConditionalGeneration, AutoProcessor
import torch
import os
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

CACHE_DIR = "/app/transformers_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
os.environ["TRANSFORMERS_OFFLINE"] = "1"

model_id = "unsloth/Llama-3.2-11B-Vision-Instruct-bnb-4bit"
model = MllamaForConditionalGeneration.from_pretrained(
    model_id,
    cache_dir=CACHE_DIR,
    torch_dtype=torch.bfloat16,
    revision="25bca24a9e42116fe4a687fba648124be4af45f6",
    trust_remote_code=True,
    device_map="auto",
)
processor = AutoProcessor.from_pretrained(model_id, cache_dir=CACHE_DIR)

@app.post("/v1/chat/completions")
async def inference(
    image: UploadFile = File(...),
    query: str = Form(...),
    context: str = Form(""),
    few_shot_images: List[UploadFile] = File([]),
    few_shot_texts: List[str] = Form([]),
    few_shot_outputs: List[str] = Form([]),
):
    def load_image(upload_file: UploadFile) -> Image.Image:
        img_path = f"/tmp/{upload_file.filename}"
        with open(img_path, "wb") as f:
            f.write(upload_file.file.read())
        return Image.open(img_path).convert("RGB")

    if not torch.cuda.is_available():
        return {"result": "GPU not available. Sorry cannot proceed further"}

    messages = []
    images = []

    for img_file, txt, out in zip(few_shot_images, few_shot_texts, few_shot_outputs):
        images.append(load_image(img_file))
        messages.append({"role": "user", "content": [{"type": "image"}, {"type": "text", "text": txt.strip()}]})
        messages.append({"role": "assistant", "content": out.strip()})

    images.append(load_image(image))
    messages.append({
        "role": "user",
        "content": [
            {"type": "image"},
            {"type": "text", "text": f"{context.strip()} {query.strip()}"}
        ]
    })

    input_text = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(
        images=[images],
        text=input_text,
        add_special_tokens=False,
        return_tensors="pt"
    ).to(model.device)

    output = model.generate(**inputs, max_new_tokens=300)
    result = processor.decode(output[0], skip_special_tokens=True)
    final_response = result.strip().split("assistant")[-1].strip()

    torch.cuda.empty_cache()
    return {"result": final_response}
