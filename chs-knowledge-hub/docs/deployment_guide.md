# Deployment Guide

This guide provides instructions on how to deploy and run the full CHS platform using Docker and Docker Compose. This is the recommended method for getting all services running quickly for development and testing.

## Prerequisites

- **Docker**: You must have Docker installed and running on your system. [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: You must have Docker Compose installed. It is included with most Docker Desktop installations. [Install Docker Compose](https://docs.docker.com/compose/install/)
- **Git**: You need Git to clone the repository.

## 1. Clone the Repository

First, clone the CHS platform repository to your local machine:

```bash
git clone <repository_url>
cd CHS/
```

## 2. Dockerfile Placeholders

For this deployment to work, each service needs a `Dockerfile`. While these are not yet implemented, here are the recommended minimal `Dockerfile`s you would place in each service directory (`chs-scada-dispatch/`, `chs-twin-factory/backend/`, `chs-hmi/`).

**Dockerfile for Python Services (`chs-scada-dispatch` and `chs-twin-factory/backend`)**

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# For chs-twin-factory, you might need to specify the backend directory
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Dockerfile for HMI (`chs-hmi`)**

```dockerfile
# Dockerfile
FROM node:18

WORKDIR /app

COPY package.json ./
COPY package-lock.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

## 3. Using Docker Compose

A `docker-compose.yml` file is provided at the root of this repository. This file is configured to build the Docker images for each service and run them together.

To start the entire platform, run the following command from the root directory of the repository:

```bash
docker-compose up --build
```

- `--build`: This flag tells Docker Compose to build the images from the Dockerfiles before starting the containers. You only need to use this the first time or when you make changes to a service's `Dockerfile` or dependencies.

## 4. Accessing the Services

Once the containers are running, you can access the different parts of the platform at the following URLs:

- **HMI (Frontend)**: [http://localhost:3000](http://localhost:3000)
- **SCADA Dispatch API Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **Twin Factory API Docs**: [http://localhost:8002/docs](http://localhost:8002/docs)

## 5. Shutting Down

To stop all the running services, press `Ctrl+C` in the terminal where `docker-compose up` is running.

To stop and remove the containers completely, you can run:

```bash
docker-compose down
```
This will stop and remove the containers, but any data written to volumes (if configured) or your local source code will be preserved.
