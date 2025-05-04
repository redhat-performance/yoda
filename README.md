# yoda
Tool to automate release readouts generation for OCP performance testing. Also implementation is decoupled in such a way that it can be used for any readout generation.

## **Prerequisites**
* Python 3.12
* Grafana login
* Use a Personal(non Red Hat Org) account due to company security restriction, we are not allowed to make documents or files as public, 
this script uploads report screenshots to your drive and make it public to be referred(hyperlinked) within slides.
* Create a project in your own google account using console. And make a note of the credentials that have access to goole drive and slides APIs.
More details [here](https://developers.google.com/slides/api/quickstart/python).
* Publish the App to make it external so script can have full access to write and read information to drive
* Google slides and drive credentials with temporary external access (i.e use your own account). This is required only if you need to update your existing slides.

## **Build & Install**
Please follow the below steps for installation.
```
>> git clone <repository_url>
>> python3 -m venv venv
>> source venv/bin/activate
>> pip install -r requirements.txt
>> export HF_TOKEN = <your-hugging-face-token>
>> pip install .
```

## **Containerized Build & Install**
If building from scratch, execute the below command.
```
podman build -f Dockerfile -t=<your-registry>/<repo>/yoda:latest .
```
Once you have your image built either in remote regristry or local, execute a container by mounting google auth token.
```
podman run --rm -it -v $(pwd)/token.json:/tmp/app/token.json:Z <your-registry>/<repo>/yoda:latest /bin/sh
sh-5.2# ls
LICENSE  README.md  build  config  main.py  requirements.txt  setup.py	src  utils  venv  vqa-app  yoda.egg-info
sh-5.2# pwd
/home/yoda
sh-5.2# source venv/bin/activate
(venv) sh-5.2# yoda --help
Usage: yoda [OPTIONS] COMMAND [ARGS]...

  yoda is the cli tool to auto generate readouts.

Options:
  --help  Show this message and exit.

Commands:
  generate              sub-command to generate a grafana panels and...
  preview-dashboard     sub-command to preview a grafana dashboard.
  preview-presentation  sub-command to preview a presentation.
  update-presentation   sub-command to update a presentation. 
```
**Note**: Please make sure that you have your google `token.json` already generated using [preview-presentation](https://github.com/redhat-performance/yoda?tab=readme-ov-file#preview-dashboard-sub-command) subcommand in your local before going with the containerized execution of yoda. Otherwise you might run into browser redirection issues while interacting with google slides because it isn't supported by any container.

## **Usage**

### Default Workflow
Once we have all the above steps figured out and everything setup correctly as day 1 operations, please execute the below command as the default workflow.

**Note**: This workflow uses the mapping defined in [config](https://github.com/redhat-performance/yoda/tree/main/config) folder as default ones. Also looks for `credentails.json` in your root directory for google oauth.
```
yoda generate --concurrency 100 --presentation '14Sn9jMWjfmqhzUglSZKmFnLSaYDVz4Kaekp0hEAj0Zg' --debug
```

### [generate] sub-command
```
Usage: yoda generate [OPTIONS]

  sub-command to generate a grafana panels and infer them. Optionally executes
  the default worklfow to publish those results to a presentation.

Options:
  --config TEXT                Path to the configuration file
  --debug                      log level
  --concurrency                To enable concurrent operations
  --inference                  Flag for inference
  --inference-endpoint TEXT    Inference endpoint
  --inference-api-key TEXT     Api key to access inference endpoint
  --inference-model TEXT       Hosted model at the inference endpoint
  --inference-model-type TEXT  Hosted model type for inference
  --csv TEXT                   .csv file path to output
  --presentation TEXT          Presentation id to parse
  --credentials TEXT           Google oauth credentials path
  --slidemapping TEXT          Slide content mapping file
  --help                       Show this message and exit.
```
Here is a simple example to trigger this command
```
>> yoda generate --config config.yaml
```

And the config.yaml follows the below YAML structure. [Example](https://github.com/redhat-performance/yoda/blob/main/config/grafana_config.yaml)
```
grafana :
  - alias: 'perfscale dev grafana'
    url: 'https://your-grafana.com:3000'
    username: 'XXXXXX'
    password: 'XXXXXX'

    dashboards:
    - alias: 'ingress-perf edge'
      raw_url: 'https://your-grafana.com:3000/d/dashboard'
      output: 'ingress_perf_panels'
      panels:
        - alias: 'RPS edge'
          id: 91
          name: 'RPS edge'
          height: 244 # Default is 720 px (px = 96 * cm)
          width: 1153 # Default is 1024 px (px = 96 * cm)
          context: 'RPS metric for edge termination'
        - alias: 'Average latency usage edge'
          id: 98
          name: 'avg_lat_us edge'
          context: 'Average latency usage for edge termination'
```
We can specify a list of grafana instances along with a list of grafana dashboards. In each dashboard, we can specify a list of panels to be scraped and exported to an `output` directory. Providing `context` to a panel is fully optional.

Each panel is uniquely identified using panel id (.i.e `id`) or its name (.i.e. `name`). Its usually recommended to use panel ids as they are very unique.

As a user if you are unsure about panel ids in your dashboard, please use preview-dashboard subcommand for a preview. Results can be exported to a csv using `--csv` option.
### [preview-dashboard] sub-command
```
yoda preview-dashboard --help
Usage: yoda preview-dashboard [OPTIONS]

  sub-command to preview a grafana dashboard.

Options:
  --url TEXT       Grafana dashboard url to preview
  --username TEXT  username of the dashboard
  --password TEXT  password of the dashboard
  --csv TEXT       .csv file path to output
  --help           Show this message and exit.

```
Here is an example usage
```
>> yoda preview-dashboard --url grafana_url --username XXXXXX --password XXXXXX
```
This will give us an output as below

```
+----------+------------------+
| Dashboard: | Panel Name     |
+------------+----------------+
+------------+----------------+
| Panel ID   | Panel Name     |
+------------+----------------+
|    1       | CPU Usage      |
|    2       | Memory Usage   |
|    3       | Disk I/O       |
|    4       | Network Traffic|
+----------+-----------------+
```
Based on this information a user should be able to prepare their config with a list of panel ids to be scraped.

### **Multi Processing**
`yoda generate` sub-command can use multiprocessing to perform all the actions in parallel. By default it spawns 75% of the cpu core number of threads in parallel to speed up its activity.
```
>> yoda generate --config config.yaml --concurrency
```
The above command now triggers 75% of active cpu core threads to execute its tasks.

## Inference

### **Default Inference** (Requires GPU with memory > 16GB)
We also have `--inference` as an optional flag that can be enabled while you execute `yoda generate` sub-command. Example usage
```
>> yoda generate --config config.yaml --debug --inference
```
At present, we are using [unsloth/Llama-3.2-11B-Vision-Instruct-bnb-4bit](https://huggingface.co/unsloth/Llama-3.2-11B-Vision-Instruct-bnb-4bit) as our default inference endpoint [hosted on an AI cluster](https://github.com/redhat-performance/yoda/tree/main/vqa-app#readme) to summarize the image. Here is how the output of updated panel data looks like after the inference.

#### **Output**
```
{"result":"The image shows a bar chart with two bars, each representing a different RPS (Requests Per Second) edge value. The top bar is green and has a value of 8.03k req/s, while the bottom bar is yellow and has a value of 9.01k req/s.\n\nThe chart appears to be comparing the performance of two different RPS edges, with the yellow bar indicating a higher performance than the green bar. The exact meaning of the chart is unclear without more context, but it seems to be highlighting the difference in performance between the two RPS edges."}
``` 

At the end `yoda generate` sub-command spits out a csv file called `panel_inference.csv` that a user can take a look at. 

Alongside the default inference endpoint that we manage, users can also have the flexibility to bring their own inference endpoint details using `inference-endpoint`, `inference-api-key`, `inference-model` and `inference-model-type` parameters.

### Supported custom inference types and their examples
### 1. vLLM
#### Host your model
```
podman run  -v ~/.cache/huggingface:/root/.cache/huggingface --env "HUGGING_FACE_HUB_TOKEN=<YOUR_TOKEN>" -p 8000:8000 --ipc=host  quay.io/vchalla/vllm-openai-cpu:latest --model llava-hf/llava-v1.6-mistral-7b-hf
```
#### Yoda Usage
```
yoda generate --config ~/config.yaml --inference --inference-endpoint <YOUR_URL> --inference-api-key <YOUR_API_KEY> --inference-model llava-hf/llava-v1.6-mistral-7b-hf --inference-model-type vllm
```
**Note**: Please make sure that your vLLM hosted model responds through calls in the below format.
```
curl -X POST http://0.0.0.0:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llava-hf/llava-v1.6-mistral-7b-hf",
    "messages": [
      {
        "role": "user",
        "content": [
          { "type": "text", "text": "What is happening in this image?" },
          { "type": "image_url", "image_url": { "url": "data:image/png;base64,<YOUR_BASE64_ENCODED_IMAGE>" } }
        ]
      }
    ]
  }'
```
### 2. ollama
#### Host your model
```
ollama pull llama3.2-vision
```
#### Yoda Usage
```
yoda generate --config ~/config.yaml --inference --inference-endpoint <YOUR_URL> --inference-api-key <YOUR_API_KEY> --inference-model llama3.2-vision --inference-model-type ollama
```
**Note**: Please make sure that your ollama hosted model responds through calls in the below format.
```
curl http://localhost:11434/api/generate   -d '{
    "model": "llama3.2-vision",
    "prompt": "Whats in the image?",
    "stream": false,
    "images": ["<YOUR_BASE64_ENCODED_IMAGE>"]
  }'
```
Also we have two ollama hosted models in our grafana instance which are running on cpu. Please feel free to use them at your own risk (.i.e. very slow response times)
```
ENDPOINT                                                              | MODEL
http://ocp-intlab-grafana.rdu2.scalelab.redhat.com:11434/api/generate - llama3.2-vision
http://ocp-intlab-grafana.rdu2.scalelab.redhat.com:11434/api/generate - llava
```
### 3. llama.cpp
#### Host your model
```
/root/llama.cpp/build/bin/llama-server -m /root/llama.cpp/models/llava-v1.6-mistral-7b.Q4_K_M.gguf --host 0.0.0.0 --port 8080
```
#### Yoda Usage
```
yoda generate --config ~/config.yaml --inference --inference-endpoint <YOUR_URL> --inference-api-key <YOUR_API_KEY> --inference-model-type llama.cpp
```
**Note**: Please make sure that your ollama hosted model responds through calls in the below format.
```
curl http://ocp-intlab-grafana.rdu2.scalelab.redhat.com:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Whats in the image?",
    "images": ["<YOUR_BASE64_ENCODED_IMAGE>"]
  }'
```

## Updating Slides
#### Prerequisites
* We need to have an already existing slide template prepared. For rosa testing please use this [template](https://docs.google.com/presentation/d/1DKDv2PTaRywqYLHXK7g1NPHxHz9Sn0sX/edit#slide=id.p1). Make a copy of it and note down the `Presentation ID`.
* Make sure that you have `credentials.json` file downloaded to your local which can be used by the tool to authenticate with google APIs.

Once we have the panels and their inference ready, a user can prepare a slide content mapping configuration file and get their existing presentation template updated. Here is how the mapping file structure looksl like below. [Example](https://github.com/redhat-performance/yoda/blob/main/config/slide_content_mapping.yaml)

```
slide_info:
  g2e457098d7b_0_0:
    images:
      g2e4672f2781_0_13: 'new_image_to_be_replaced.png'
      g2e4672f2781_0_14: '../yoda/ingress_perf_panels/panel_98_Average latency usage edge.png'
    texts:
      text_id: "new text to be replaced"
```
We can simply update the presentation with our new set of local images using `update-presentation` sub-command.

### [update-presentation] sub-command
```
yoda update-presentation --help
Usage: yoda update-presentation [OPTIONS]

  sub-command to update a presentation. More details here:
  https://developers.google.com/slides/api/quickstart/python

Options:
  --id TEXT            Presentation id to preview
  --credentials TEXT   Google oauth credentials path
  --slidemapping TEXT  Slide content mapping file
  --help               Show this message and exit.
```
Here is an example usage command
```
yoda update-presentation --id '14Sn9jMWjfmqhzUglSZKmFnLSaYDVz4Kaekp0hEAj0Zg' --slidemapping config/slide_content_mapping.yaml
```

Now you might be worndering on where to get the slide and its object ids from in order to generate the slide content mapping. For that we have a `preview-presentation` sub-command as well.

### [preview-presentation] sub-command
```
yoda preview-presentation --help
Usage: yoda preview-presentation [OPTIONS]

  sub-command to preview a presentation. More details here:
  https://developers.google.com/slides/api/quickstart/python

Options:
  --id TEXT           Presentation id to preview
  --credentials TEXT  Google oauth credentials path
  --csv TEXT          .csv file path to output
  --help              Show this message and exit.
```
Here is a example usage
```
yoda preview-presentation --id '14Sn9jMWjfmqhzUglSZKmFnLSaYDVz4Kaekp0hEAj0Zg'
```
The output is logged in a tabular format to the console. Can also be exported to a csv file using `--csv` option
```
--------------------------------------------------------------------------
--------------------------------------------------------------------------
Slide Number | Slide ID | Slide Data
--------------------------------------------------------------------------
--------------------------------------------------------------------------
1	     |  p1	    | {   "images": {     "p1_i889": "https://image_url"   },   "texts": {     "p1_i887": "\n",     "p1_i888": "\nOpenShift 4.15 Perf/Scale Test Report on ROSA\n OpenShift  Performance and Scale Team \n \n#forum-ocp-perfscale on Slack\n \n\n \n\n",     "p1_i890": "Red Hat Confidential\n"   } }
--------------------------------------------------------------------------
2            |  p2	    | {   "images": {     "p1_i889": "https://image_url"   },   "texts": {     "p1_i887": "\n",     "p1_i888": "\nOpenShift 4.15 Perf/Scale Test Report on ROSA\n OpenShift  Performance and Scale Team \n \n#forum-ocp-perfscale on Slack\n \n\n \n\n",     "p1_i890": "Red Hat Confidential\n"   } }
```
