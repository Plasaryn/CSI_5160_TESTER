import socket
import uvicorn
import httpx
import json
from job import Job
from fastapi import FastAPI, HTTPException
from objects import Job as IncomingJob, Host


HOSTNAME: str  = socket.gethostname()

app: FastAPI = FastAPI()

HOSTS: dict[str, Host] = {}

JOBS: dict[int, Job] = {}

# A Batch Job is a collection of jobs that are 
# performed on multiple hosts. Each Batch Job
# Has its own index, and can reference
# other jobs running on other registered hosts
BATCH_JOBS: dict[int, list[dict[str, int]]] = {}

@app.get("/")
async def index():
  return {
    "status": "active",
    "hostname": HOSTNAME
  }

@app.post("/host")
async def add_host(host: Host):
  hostname = host.hostname
  if hostname in HOSTS.keys():
    raise HTTPException(status_code=409, detail="Hostname already present")
  HOSTS[hostname] = host
  return {"Message": "Host Successfully Registered"}

@app.get("/host/{hostname}")
async def get_host(hostname: str):
  if hostname not in HOSTS:
    raise HTTPException(status_code=404, detail="Hostname does not exist")
  host = HOSTS[hostname]
  return host.__dict__

@app.put("/host/{hostname}")
async def put_host(hostname: str, host: Host):
  if hostname not in HOSTS:
    raise HTTPException(status_code=404, detail="Hostname does not exist")
  HOSTS[hostname] = host
  return {"Message": "Hostname was successfully updated"}
  

@app.delete("/host/{hostname}")
async def delete_host(hostname: str):
  if hostname not in HOSTS:
    raise HTTPException(status_code=404, detail="Hostname does not exist")
  HOSTS.pop(hostname)
  return {"Message": "Host successfully deleted"}


@app.get("/hosts")
async def get_hosts():
  return {"hosts": HOSTS}

@app.get("/job/{id}")
async def get_job(id: int):
  if id not in JOBS:
    raise HTTPException(status_code=404, detail="Job ID not present")
  return JOBS[id].get_results()

@app.post("/job", status_code=201)
async def new_job(incoming_job: IncomingJob):
  temp: Job = Job(HOSTNAME, **incoming_job.__dict__)
  id: int = temp.get_id()
  JOBS[id] = temp
  return {
    "Message": "New Job Successfully created",
    "new_job_id": id
  }

@app.put("/job/{id}")
async def put_job(id: int):
  raise HTTPException(status_code=403, detail="Forbidden")

@app.delete("/job/{id}")
async def delete_job(id: int):
  raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/batch-job")
async def new_batch_job(incoming_job: IncomingJob):
  to_reply: dict = {}
  if len[HOSTS] == 1:
    to_reply["Warning"] = (
      "Only one host registered"
    )
  elif not HOSTS:
    raise HTTPException(status_code=406, detail="No hosts registered, cannot run batch.")
  
  # Register a new ID for BATCH_JOBS
  id: int = len(BATCH_JOBS) + 1

  # Enroll a blank slate in Batch Jobs
  BATCH_JOBS[id] = []

  to_reply["registration_failed"] = []

  # For each host, start a new job
  for host in HOSTS:
    r = httpx.post(
      f"{host['address']}/job",
      data = incoming_job.__dict__
    )

    if r.status_code == 201:
      response_body: dict = json.loads(r.text)
      BATCH_JOBS[id].append(
        {host["address"] : response_body.get("new_job_id")}
      )
    else:
      to_reply["registration_failed"] += [host["hostname"]]

  # Check the progress of adding hosts to the batch.
  if not BATCH_JOBS[id]:
    raise HTTPException(500, "Could not start batch from Hosts")
  
  return {
    "Message": "Batch created successfully",
    "new_batch_id": id
  }

@app.get("/batch-job/{id}")
async def get_batch_job(id: int):
  if id not in BATCH_JOBS:
    raise HTTPException(status_code=404, detail="Batch Job not found")
  
  # Aggregate all batches
  aggregate: list[dict] = []

  for job in BATCH_JOBS[id]:
    r = httpx.get(
      f"{job.keys()[0]}/job/{job.values()[0]}"
    )

    if r.status_code == 200:
      aggregate.append(json.loads(r.text))
    else:
      raise HTTPException(status_code=500, detail="Could not fetch job")
  
  return aggregate

if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=8000)