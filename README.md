# insight-creator
Tool to automate release readouts generation for OCP performance testing.

## **Prerequisites**

* [Hugging Face](https://huggingface.co/) Account
* Grafana login

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
Here is a simple command to trigger this tool
```
>> insight-creator --config config.yaml
```

And the config.yaml follows the below YAML structure. [Example](https://github.com/vishnuchalla/insight-creator/blob/main/config/insight-creator.yaml)
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
          context: 'RPS metric for edge termination'
        - alias: 'Average latency usage edge'
          id: 98
          name: 'avg_lat_us edge'
          context: 'Average latency usage for edge termination'
```
We can specify a list of grafana instances along with a list of grafana dashboards. In each dashboard, we can specify a list of panels to be scraped and exported to an `output` directory. Providing `context` to a panel is fully optional.

Each panel is uniquely identified using panel id (.i.e `id`) or its name (.i.e. `name`). Its usually recommended to use panel ids as they are very unique.

As a user if you are unsure about panel ids in your dashboard, please use `expand: true` in your config file as below to get a preview of panels and their corresponsind ids.
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
      expand: true
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
insight-creator uses multiprocessing to perform all the actions in parallel. By default it uses 75% of the cpu cores to speed up its tasks which can also be regulated by the below flag
```
>> insight-creator --config config.yaml --concurrency 100
```
The above command now tells the tool to use 100% of cpu cores to execute its taks.

### **Inference**
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