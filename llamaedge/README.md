# LlamaEdge API Server with Meta Llama 3 Models

This project provides Dockerfiles to build and run the LlamaEdge API server with Meta Llama 3.1 8B Instruct and Llama 3.2 3B Instruct models using WasmEdge. The API server will be accessible on port 8080.

## Prerequisites

- Docker installed on your local machine or EC2 instance.
- Sufficient resources (RAM and CPU).
  - **Llama 3.1 8B model**: Requires significant RAM (e.g., 32GB+ recommended).
  - **Llama 3.2 3B model**: Requires less RAM (e.g., 8GB+ recommended).
  - **A `t2.micro` EC2 instance (1 GiB RAM) is NOT sufficient for either model.**

## Building the Docker Images

1.  **Clone the repository or ensure the Dockerfiles are in your current directory.**
2.  **Navigate to the directory containing the Dockerfiles.**
3.  **Build the desired Docker image:**

    - For Llama 3.1 8B Instruct (using `Dockerfile.llama3.1-8b`):
      ```bash
      docker build -t llamaedge-api-8b -f Dockerfile.llama3.1-8b .
      ```
    - For Llama 3.2 3B Instruct (using `Dockerfile.llama3.2-3b`):
      `bash
    docker build -t llamaedge-api-3b -f Dockerfile.llama3.2-3b .
    `
      The build process will download the Wasm application and the respective LLM, which may take time.

## Running the Docker Container

### Running Locally

- To run the Llama 3.1 8B server:
  ```bash
  docker run -d -p 8080:8080 --name llamaedge-server-8b llamaedge-api-8b
  ```
- To run the Llama 3.2 3B server:
  ```bash
  docker run -d -p 8080:8080 --name llamaedge-server-3b llamaedge-api-3b
  ```
  - `-d`: Detached mode.
  - `-p 8080:8080`: Maps host port 8080 to container port 8080.
  - `--name`: Assigns a name to the container.

### Running on an EC2 Instance

1.  **Launch an EC2 Instance:**

    - Choose an AMI (e.g., Amazon Linux 2, Ubuntu Server).
    - **Select an appropriate instance type based on the model's RAM requirements.**
    - Configure security groups to allow inbound TCP traffic on port `8080`.
    - Ensure Docker is installed on the instance (refer to AWS documentation or use user data scripts).

2.  **Connect to your EC2 instance via SSH.**

3.  **Build the image directly on EC2 or pull a pre-built image from a registry (e.g., Docker Hub):**

    - If building on EC2, use the `docker build` commands from above.
    - If pulling from Docker Hub (replace `your-dockerhub-username` and `tag`):
      ```bash
      # docker pull your-dockerhub-username/llamaedge-api-8b:latest
      # docker pull your-dockerhub-username/llamaedge-api-3b:latest
      ```

4.  **Run the Docker container on EC2 (use the appropriate image name):**
    ```bash
    # For 8B model
    # docker run -d -p 8080:8080 --name llamaedge-server-8b llamaedge-api-8b
    # For 3B model
    # docker run -d -p 8080:8080 --name llamaedge-server-3b llamaedge-api-3b
    ```

## Accessing the API

The API server will be available at `http://<your-ec2-instance-public-ip>:8080` or `http://localhost:8080`.

Note: You may need to adjust your security group settings to allow inbound traffic on port 8080.

Example chat completion request (adjust `"model"` field as per the running server):

```bash
curl http://<your-ip-or-localhost>:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Llama-3.1-8b",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "What is the weather like in Boston?"
      }
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_current_weather",
          "description": "Get the current weather in a given location",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA"
              },
              "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"]
              }
            },
            "required": ["location"]
          }
        }
      }
    ],
    "tool_choice": "auto",
    "temperature": 0.7,
    "max_tokens": 150
  }'
```

## Stopping the Container

```bash
# For 8B server
# docker stop llamaedge-server-8b
# docker rm llamaedge-server-8b

# For 3B server
# docker stop llamaedge-server-3b
# docker rm llamaedge-server-3b
```
