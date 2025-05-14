import json
import base64
import requests
import logging

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
    query, inference_endpoint, inference_api_key, inference_model, inference_model_type, few_shot_file_path, samples_count = args
    system_prompt = """
    You are a Kubernetes/OpenShift performance engineer focussed on finding performance differences and regressions in new releases compared to older ones.
    """
    context = each_panel['panel_context'] if 'panel_context' in each_panel else ""
    if few_shot_file_path:
        try:
            with open(few_shot_file_path, "r") as f:
                data = json.load(f)
                all_examples = data.get("examples", [])
                selected_examples = all_examples[:samples_count]
                formatted_examples = []
                for ex in selected_examples:
                    formatted = (
                        f"[Image (base64)]: {ex['image_b64']}\n"
                        f"[Query]: {ex['query']}\n"
                        f"[Answer]: {ex['answer']}\n"
                        f"[Explanation]: {ex['explanation']}"
                    )
                    formatted_examples.append(formatted)
                few_shot_text = "\n\n".join(formatted_examples)
                logger.info(f"Loaded {len(selected_examples)} few-shot examples from {few_shot_file_path}")
        except Exception as e:
            logger.warning(f"Could not load few-shot examples: {e}")
        query = f"{few_shot_text}\n\n{query}"
    default_inference_endpoint = "http://q42-h03-dgx.rdu3.labs.perfscale.redhat.com:30080/v1/chat/completions"
    inference_endpoint = inference_endpoint or default_inference_endpoint

    if inference_endpoint == default_inference_endpoint:
        files = {
            'image': open(each_panel["panel_image"], 'rb')
        }
        data = {
            'context': context,
            'query': query,
        }
        try:
            logger.info(f"Running default inference for image: {each_panel["panel_image"]}")
            response = requests.post(inference_endpoint, files=files, data=data)
            response.raise_for_status()
            each_panel['panel_text'] = response.text
            return_dict[idx] = each_panel
            files['image'].close()
            return
        except Exception as err:
            logger.info(f"Unexpected error from default inference: {err}")
        finally:
            files['image'].close()
    
    with open(each_panel["panel_image"], "rb") as img_file:
        image_b64 = base64.b64encode(img_file.read()).decode("utf-8")

    payload = {}
    url = f""    
    match inference_model_type:
        case "vllm":
            payload = {
                "model": inference_model,
                "messages": [
                    {"role": "system", "content": system_prompt} if system_prompt else {},
                    {"role": "user", "content": [
                        {"type": "text", "text": f"{context}\n\n{query}" if context else query},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}} if image_b64 else {}
                    ]}
                ],
            }
            payload["messages"] = [msg for msg in payload["messages"] if msg]
            url = f"{inference_endpoint}/v1/chat/completions"

        case "ollama":
            prompt = f"{system_prompt}\n\n{context}\n\n{query}" if system_prompt else f"{context}\n\n{query}" if context else query
            payload = {
                "model": inference_model,
                "prompt": prompt,
                "stream": False,
            }
            if image_b64:
                payload["images"] = [image_b64]
            url = f"{inference_endpoint}/api/generate"

        case "llama.cpp":
            prompt = f"{system_prompt}\n\n{context}\n\n{query}" if system_prompt else f"{context}\n\n{query}" if context else query
            payload = {
                "prompt": prompt,
                "stream": False,
            }
            if image_b64:
                payload["images"] = [image_b64]
            url = f"{inference_endpoint}/completion"

        case _:
            logger.info(f"Unsupported model_type: {inference_model_type}")
            return

    try:

        logger.info(f"Running inference for image: {each_panel["panel_image"]}")
        payload["top_p"] = 0.95
        payload["frequency_penalty"] = 1.03
        payload["temperature"] = 0.01
        payload["max_tokens"] = 512
        payload["verbose"] = True
        logger.debug(f"Sending payload: {payload}")
        headers = {"Content-Type": "application/json"}
        if inference_api_key:
            headers["Authorization"] = f"Bearer {inference_api_key}"
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        if "response" in response_json.keys():
            each_panel['panel_text'] = response_json["response"]
        elif "content" in response_json.keys():
            each_panel['panel_text'] = response_json["content"]
        elif "choices" in response_json.keys() and len(response_json["choices"]) > 0:
            each_panel['panel_text'] = response_json["choices"][0]["message"]["content"]
        return_dict[idx] = each_panel
        return
    except Exception as err:
        logger.info(f"Unexpected error from inference: {err}")
