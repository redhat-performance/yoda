from transformers import Pix2StructProcessor, Pix2StructForConditionalGeneration
import requests
from PIL import Image

def google_deplot(image_paths: list, query: str):
    processor = Pix2StructProcessor.from_pretrained('google/deplot', legacy=False)
    model = Pix2StructForConditionalGeneration.from_pretrained('google/deplot')

    image = Image.open(image_paths[0])

    inputs = processor(images=image, text=query, return_tensors="pt")
    predictions = model.generate(**inputs, max_new_tokens=512)
    decoded_version = processor.decode(predictions[0], skip_special_tokens=True)
    print(type(decoded_version))
    print(decoded_version)
