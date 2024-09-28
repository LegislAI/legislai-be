# Legislai Backend


## Installation

### Requirements:

- [Python](https://www.python.org/)
- [Docker](https://www.docker.com/)

### Dependencies

Install the project dependencies by running the following command:

```bash
pip install -r requirements.txt
```


## Setup
**Note:** Run all commands from the `legislai-be` directory.

1. Create a `.env` file in the root of the project with the following content, by copying the `.env.example` file:

    ```bash
    cp .env.example .env
    ```

2. Start the Docker Containers

    To set up and start the necessary services, run the following command:

    ```bash
    docker compose up -d


### Accessing Neo4j

Once the Docker containers are running, you can access the Neo4j database via its web interface:

1. Open your browser and navigate to http://localhost:7474.
2. Log in using the following credentials:
    - Username: neo4j
    - Password: password

This will take you to the Neo4j browser, where you can run Cypher queries and manage the graph database.
