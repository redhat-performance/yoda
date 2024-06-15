from transformers import Pix2StructProcessor, Pix2StructForConditionalGeneration
from PIL import Image
import torch
from torch.cuda.amp import autocast

def image_deplot(each_panel: dict, args: tuple, return_dict: dict, idx: int) -> None:
    """
    Deplots the image and generates its underlying table.

    Args:
        each_panel (dict): panel reference to update
        args (tuple): arguments to read
        return_dict (dict): shared dictionary across the threads
        idx (int): unique index to store thread data

    Returns:
        None
    """
    query = args
    processor = Pix2StructProcessor.from_pretrained('google/deplot', legacy=False)
    model = Pix2StructForConditionalGeneration.from_pretrained('google/deplot')

    if torch.cuda.is_available():
        device = torch.device('cuda')
        model.to(device)
    else:
        device = torch.device('cpu')
    
    image = Image.open(each_panel['panel_image'])

    # Process the image and move to GPU if available
    inputs = processor(images=image, text=query, return_tensors="pt").to(device)

    try:
        # Use autocast for mixed precision to save memory
        with autocast():
            predictions = model.generate(**inputs, max_new_tokens=512)
        
        # Process the predictions
        decoded_output = processor.decode(predictions[0], skip_special_tokens=True)
        decoded_output = decoded_output.replace('<0x0A>', '\n')
        data_lines = [line.strip() for line in decoded_output.strip().split('\n')]
        table = data_lines[0] + "" + data_lines[1] + "\n" + "\n".join(data_lines[2:])
        each_panel['panel_text'] = table

    except torch.cuda.OutOfMemoryError:
        print("CUDA out of memory. Clearing cache and retrying...")
        torch.cuda.empty_cache()
        return_dict[idx] = {"error": "CUDA out of memory"}
    
    # Free up memory
    del inputs
    torch.cuda.empty_cache()

    return_dict[idx] = each_panel
