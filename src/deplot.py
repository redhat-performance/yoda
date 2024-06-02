from transformers import Pix2StructProcessor, Pix2StructForConditionalGeneration
from PIL import Image

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

    image = Image.open(each_panel['image_path'])

    inputs = processor(images=image, text=query, return_tensors="pt")
    predictions = model.generate(**inputs, max_new_tokens=512)
    decoded_output = processor.decode(predictions[0], skip_special_tokens=True)

    decoded_output = decoded_output.replace('<0x0A>', '\n')
    data_lines = [line.strip() for line in decoded_output.strip().split('\n')]
    table = data_lines[0] + "" + data_lines[1] + "\n" + "\n".join(data_lines[2:])
    each_panel['data_table'] = table

    return_dict[idx] = each_panel
