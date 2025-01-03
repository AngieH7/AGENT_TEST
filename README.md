# AGENT_TEST

This project is a playground to better understand the agentic workflow and graph rag.

This work is creating an customer service agent which can answer any product policy questions from the client throught interface. 
This work will only focus on the agent part. It is assuming the policies have been stored in the relevant database already. 
The workflow has been displayed as below. 

![Alt text](./A5AD6FAD-AB91-4A97-A340-C646FF5A86FF.png?raw=true "Optional Title")

The agent component design is shown down below.

![Alt text](./Screenshot.png?raw=true "Optional Title")



## Python Script: `customer_service_agent.py`

The `customer_service_agent.py` script is the core component of this project. It is responsible for processing client queries and providing accurate responses based on the stored product policies.

### Key Features:
- **Natural Language Processing (NLP):** Utilizes NLP techniques to understand and interpret client questions.
- **Response Generation:** Constructs and delivers appropriate responses to client queries.

### How to Run:
1. Ensure all dependencies are installed:
    ```bash
    pip install -r requirements.txt
    ```
2. Execute the script:
    ```bash
    python customer_service_agent.py
    ```
