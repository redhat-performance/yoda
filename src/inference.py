from PIL import Image
from transformers import AutoModel, AutoTokenizer
import logging
import torch
from torch.cuda.amp import autocast

logger = logging.getLogger(__name__)

def image_inference(each_panel: dict, args: tuple, return_dict: dict, idx: int) -> None:
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

    if torch.cuda.is_available():
        logger.info(f"GPU detected. Proceeding with inference for image: {each_panel["panel_image"]}")
    else:
        logger.info(f"No GPU detected. Sorry cannot run inference for image: {each_panel["panel_image"]}")
        return_dict[idx] = each_panel
        return

    image = Image.open(each_panel['panel_image']).convert('RGB')
    context = each_panel['panel_context'] if 'panel_context' in each_panel else ""
    input_prompt = f"{context}\nQuestion: {query}"
    msgs = [{'role': 'user', 'content': input_prompt}]

    try:
        model = AutoModel.from_pretrained('openbmb/MiniCPM-Llama3-V-2_5', trust_remote_code=True, torch_dtype=torch.float16)
        model = model.to(device='cuda')
        tokenizer = AutoTokenizer.from_pretrained('openbmb/MiniCPM-Llama3-V-2_5', trust_remote_code=True)
        model.eval()

        # Use autocast for mixed precision to save memory
        with autocast():
            res = model.chat(
                image=image,
                msgs=msgs,
                tokenizer=tokenizer,
                sampling=True,
                temperature=0.7,
                system_prompt="You are an expert in analysing openshift performance metrics",
                )
        each_panel['panel_text'] = res

    except torch.cuda.OutOfMemoryError:
        print("CUDA out of memory. Clearing cache and retrying...")
        torch.cuda.empty_cache()
        each_panel['panel_text'] = "error: CUDA out of memory"
        return_dict[idx] = each_panel
    
    # Free up memory
    torch.cuda.empty_cache()

    return_dict[idx] = each_panel

