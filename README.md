gcloud-logs
===========

Download and tail (stream) Stackdriver logs for specific Google Compute Engine instances directly into your console.

Example
=======

Tails logs from two GCE instances named "machine1" and "machine2":

```shell
gcloud_logs machine1 machine2 --tail 
```

Installing
==========

With pip:

```shell
pip install git+https://github.com/gmega/gcloud_logs
```

This project has been tested in Python 3.7 and later. 



