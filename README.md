# yoda
Tool to automate release readouts generation for OCP performance testing. Also implementation is decoupled in such a way that it can be used for any readout generation.

## **Prerequisites**

* [Hugging Face](https://huggingface.co/) Account
* Grafana login
* Google slides and drive credentials with temporary external access (i.e use your own account). This is required only if you need to update your existing slides.

## **Build & Install**
Once you obtain the [Hugging Face Token](https://www.youtube.com/watch?v=Br7AcznvzSA) for your account, Please follow the below steps for installation.
```
>> git clone <repository_url>
>> python3 -m venv venv
>> source venv/bin/activate
>> pip install -r requirements.txt
>> export HF_TOKEN = <your-hugging-face-token>
>> pip install .
```

## **Usage**
### Generate sub-command
```
yoda generate --help
Usage: yoda generate [OPTIONS]

  sub-command to extract grafana panels and infer them. Optionally executes the default worklfow to publish those results to a presentation.

Options:
  --config TEXT          Path to the configuration file
  --debug                log level
  --concurrency INTEGER  Number of concurrent processes
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
          height: 244 # Default is 720 px
          width: 1153 # Default is 1024 px
          context: 'RPS metric for edge termination'
        - alias: 'Average latency usage edge'
          id: 98
          name: 'avg_lat_us edge'
          context: 'Average latency usage for edge termination'
```
We can specify a list of grafana instances along with a list of grafana dashboards. In each dashboard, we can specify a list of panels to be scraped and exported to an `output` directory. Providing `context` to a panel is fully optional.

Each panel is uniquely identified using panel id (.i.e `id`) or its name (.i.e. `name`). Its usually recommended to use panel ids as they are very unique.

As a user if you are unsure about panel ids in your dashboard, please use preview-dashboard subcommand for a preview. Results can be exported to a csv using `--csv` option.
### Preview sub-command
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
`yoda generate` sub-command uses multiprocessing to perform all the actions in parallel. By default it spawns 75% of the cpu core threads in parallel to speed up its activity which can also be regulated by the below flag
```
>> yoda generate --config config.yaml --concurrency 100
```
The above command now triggers 100% of active cpu core threads to execute its tasks.

### **Inference**
We also have inference as an optional flag that can be enabled while you execute `yoda generate` sub-command. Example usage
```
>> yoda generate --config config.yaml --concurrency 100 --debug --inference
```
At present, we are using [google/deplot](https://huggingface.co/google/deplot) as our inference endpoint to summarize the image. Here is how the output of given panel data looks like after the inference.

#### **Output**
```
[
{
  "panel_id": 91,
  "panel_title": "RPS edge",
  "panel_context": "RPS metric for edge termination",
  "image_path": "ingress_perf_panels/panel_91_RPS edge.jpeg",
  "data_table": "TITLE || RPS edge\n4.14 | 43.95\n41.65 | 41.65"
},
{
  "panel_id": 98,
  "panel_title": "Average latency usage reencrypt",
  "panel_context": "Average latency usage for reencrypt termination",
  "image_path": "ingress_perf_panels/panel_98_Average latency usage reencrypt.jpeg",
  "data_table": "TITLE || avg.lat.us\n4.14 | 4.1\n36.43 ms | 36.43"
}
]
```
We are still exploring other models and will add more details soon.  
At the end `yoda generate` sub-command spits out a csv file called panel_inference.csv that a user can take a look at. 

Once we have the panels and their inference ready, a user can prepare a slide content mapping configuration file and get their existing presentation template updated.