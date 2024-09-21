# yoda
Tool to automate release readouts generation for OCP performance testing. Also implementation is decoupled in such a way that it can be used for any readout generation.

## **Prerequisites**

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

## **Usage**

### Default Workflow
Once we have all the above steps figured out and everything setup correctly as day 1 operations, please execute the below command as the default workflow.

**Note**: This workflow uses the mapping defined in [config](https://github.com/vishnuchalla/yoda/tree/main/config) folder as default ones. Also looks for `credentails.json` in your root directory for google oauth.
```
yoda generate --concurrency 100 --presentation '14Sn9jMWjfmqhzUglSZKmFnLSaYDVz4Kaekp0hEAj0Zg' --debug
```

### [generate] sub-command
```
yoda generate --help
Usage: yoda generate [OPTIONS]

  sub-command to extract grafana panels and infer them. Optionally executes the default worklfow to publish those results to a presentation.

Options:
  --config TEXT          Path to the configuration file
  --debug                log level
  --concurrency          Flag to enable concurrency
  --deplot               Flag for deplotting the image
  --inference            Flag for inference
  --csv TEXT             .csv file path to output
  --presentation TEXT    Presentation id to parse
  --credentials TEXT     Google oauth credentials path
  --slidemapping TEXT    Slide content mapping file
  --help                 Show this message and exit.
```
Here is a simple example to trigger this command
```
>> yoda generate --config config.yaml
```

And the config.yaml follows the below YAML structure. [Example](https://github.com/vishnuchalla/yoda/blob/main/config/grafana_config.yaml)
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

## Local Inference
Inference is totally optional to prepare a summary of the results, manual scrutiny is MUST to validate the statements.

## **Pre-requisites**
[Hugging Face](https://huggingface.co/) Account. This is used to use an huggingface token to download models locally. Once you obtain the [Hugging Face Token](https://www.youtube.com/watch?v=Br7AcznvzSA) for your account, Please do export it
```
export HF_TOKEN=<YOUR_TOKEN>
```

### **Deplot**
 We have `--deplot` as an optional flag that can be enabled while you execute `yoda generate` sub-command. Example usage
```
>> yoda generate --config config.yaml --concurrency --debug --deplot
```
At present, we are using [google/deplot](https://huggingface.co/google/deplot) as our deplot endpoint. Here is how the output of updated panel data looks like after the deplot.

#### **Output**
```
'TITLE | RPS edge| RPS edge\n4.14 | 43.95\n41.65 | 41.65'
```

## Remote Inference

### **Inference** (Requires GPU with memory > 16GB)
We also have `--inference` as an optional flag that can be enabled while you execute `yoda generate` sub-command. Example usage
```
>> yoda generate --config config.yaml --concurrency --debug --inference
```
At present, we are using [openbmb/MiniCPM-Llama3-V-2_5](https://huggingface.co/openbmb/MiniCPM-Llama3-V-2_5) as our inference endpoint [hosted on an AI cluster](https://github.com/vishnuchalla/yoda/tree/main/vqa-app#readme) to summarize the image. Here is how the output of updated panel data looks like after the inference.

#### **Output**
```
The image is a bar chart with two bars representing different data points. The left bar is colored green and represents a value of 4.15, while the right bar is yellow and represents a value of 4.14. Both bars have additional information displayed as text: "41.65K req/s" for the green bar and "43.95K req/s" for the yellow bar. This suggests that the chart is comparing two quantities, possibly request rates, where the yellow bar has a slightly higher value than the green bar.
``` 
#### Note: `--deplot` and `--inference` falgs are mutually exclusive. 

At the end `yoda generate` sub-command spits out a csv file called `panel_inference.csv` that a user can take a look at. 

## Updating Slides
#### Prerequisites
* We need to have an already existing slide template prepared. For rosa testing please use this [template](https://docs.google.com/presentation/d/1DKDv2PTaRywqYLHXK7g1NPHxHz9Sn0sX/edit#slide=id.p1). Make a copy of it and note down the `Presentation ID`.
* Make sure that you have `credentials.json` file downloaded to your local which can be used by the tool to authenticate with google APIs.

Once we have the panels and their inference ready, a user can prepare a slide content mapping configuration file and get their existing presentation template updated. Here is how the mapping file structure looksl like below. [Example](https://github.com/vishnuchalla/yoda/blob/main/config/slide_content_mapping.yaml)

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
