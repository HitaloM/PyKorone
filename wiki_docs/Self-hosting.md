---
icon: 🚀
title: Self-hosting Sophie
---

This guide explains how to self-host Sophie Bot using Podman and Ansible, mirroring the official production environment.

## Architecture Overview

Sophie is designed to run as a set of microservices to ensure scalability and high availability:

- **Stable Instance**: The primary bot instance that handles most user interactions. It can also act as a proxy to the Beta instance.
- **Beta Instance**: A secondary instance used for testing new features.
- **Scheduler**: Handles background tasks, timed events, and scheduled operations.
- **REST API**: Provides an interface for the web dashboard and external integrations.

All components are containerized and typically run using **Podman**.

## Prerequisites

Before starting, ensure you have the following installed on your host system:

- **Podman**: For container management.
- **Ansible**: For automated deployment.
- **MongoDB**: Persistent data storage.
- **Redis / Valkey**: For caching and FSM (Finite State Machine) storage.

## Deployment with Ansible

The recommended way to deploy Sophie is using the provided Ansible playbooks in the `deploy/` directory.

### 1. Configuration

Copy `data/config.example.env` to `data/config.env` and fill in the required values. Key variables include:

- `TOKEN`: Your Telegram Bot API token.
- `MONGO_HOST`: Connection string for MongoDB.
- `REDIS_HOST`: Hostname for Redis.

### 2. Run the Playbook

To deploy the stable environment:

```bash
ansible-playbook -i your_inventory deploy/stable.yml
```

To deploy the beta environment (includes scheduler and REST API):

```bash
ansible-playbook -i your_inventory deploy/beta.yml
```

## Running with Podman (Manual)

If you prefer to run containers manually, you can use the following logic (based on the Quadlet templates):

### Stable Instance

```bash
podman run -d \
  --name sophie-stable \
  --env-file /var/sophie/stable.env \
  -p 8071:8071 \
  registry.gitlab.com/sophiebot/sophie:stable-runtime
```

### Scheduler

The scheduler is the same image but runs with `MODE=scheduler`.

```bash
podman run -d \
  --name sophie-scheduler \
  -e MODE=scheduler \
  --env-file /var/sophie/scheduler.env \
  registry.gitlab.com/sophiebot/sophie:stable-runtime
```

### REST API

The REST API is the same image but runs with `MODE=rest`.

```bash
podman run -d \
  --name sophie-rest \
  -e MODE=rest \
  --env-file /var/sophie/rest.env \
  -p 8075:8075 \
  registry.gitlab.com/sophiebot/sophie:stable-runtime
```

## Proxy System (Stable + Beta)

Sophie implements a unique proxying system where the Stable instance can redirect traffic to the Beta instance. This allows seamless transitions and testing of new features.

- `PROXY_ENABLE`: Set to `True` to enable proxying.
- `PROXY_STABLE_INSTANCE_URL`: URL of the stable instance.
- `PROXY_BETA_INSTANCE_URL`: URL of the beta instance.

When enabled, the bot can route requests between instances based on configuration, allowing for "canary" style deployments or easy beta testing for specific users/chats.

## Environment Variables Reference

| Variable | Description |
| :--- | :--- |
| `TOKEN` | Telegram Bot Token |
| `MONGO_DB` | MongoDB Database Name |
| `REDIS_DB_FSM` | Redis Database index for FSM |
| `OWNER_ID` | Telegram User ID of the bot owner |
| `ENVIRONMENT` | Name of the environment (e.g., `production-stable`) |
| `MODE` | Set to `scheduler` for the scheduler service |

---
> For advanced configuration, refer to the `deploy/templates/` directory in the repository.
> {.is-info}
