# Overview

The goal here is to create a llm agent using llama4 to generate ansible playbooks and call endpoint to test the playbook. 

Our fastapi server should have the following endpoints:

- `GET` - `/health` - Health check endpoint
- `GET` - `/task/{task_id}` - Get the status of the playbook test process
- `POST` - `/generate-playbook` - Generate a playbook based on the *device id* and *intentions* (this will create a task id)
- `POST` - `/iteration/{task_id}` - Continue iterating on the playbook
- `POST` - `/task/{task_id}/update` - Update the task status via the backend server
- `POST` - `/process/playbook` - Process the playbook via the backend server

## Tech Stack

- FastAPI
- Docker
- [llama sdk](https://github.com/meta-llama/llama-api-python)

## Flow

- The agent will be triggered via the `/generate-playbook` endpoint with the following parameters:
    - `device_id` - The id of the device to generate the playbook for
    - `intentions` - The intentions of the playbook. what the playbook should do.

- Once the playbook is generated, the agent should call the `/process/playbook` endpoint to trigger the playbook execution via the backend server. sending as parameters:
    - `task id` - The id of the task to process
    - `playbook_content` - The content of the playbook to process

- The backend server will run the playbook against the device and generate an entry in the database with the `task id`, the `playbook_content` and the `status` of the run.

- The agent should then call the `/task/{task_id}` endpoint to get the status of the task and if the status is `success` or `failed`:
    - If the status is `failed`, the agent should call the `/iteration/{task_id}` endpoint to continue iterating on the playbook.
    - If the status is `success`, the agent should call the `/task/{task_id}/update` endpoint to update the task status in the database.

- This process will repeat until the playbook is successful or the maximum number of iterations is reached.