# **LegisAI Backend**

## 1. Project Overview

- **Main Goal**: Create a virtual assistant that simplifies search and enhances understanding of Portuguese legislation, making it accessible and understandable via a unique website
- **Problem Statement**: Accessibility and searchability within the Portuguese legal system are complex, often requiring specialized knowledge. This system addresses these challenges by offering an intuitive and efficient way to access legal information to all the people interested on it.

## 2. Context and Background

Portuguese legislation is dense and difficult to navigate for the average person. Many individuals are unaware of their rights due to the lack of accessible information. By automating search and contextualizing results, the virtual assistant empowers users to understand and apply legal information effectively.

Legislation is a complex and rapidly changing topic, which is hard to navigate for professionals and even harder for individuals.

Keeping track of your rights and duties can sometimes be hard, and harder if you have to navigate through many different places to get to your desired information.

LegislAI offers a centralized, user-friendly, AI-powered legal database, designed to simplify access and improve understanding of Portuguese legislation.

## 3. Technical Details

- **Infrastructure**: All infrastructure is deployed and managed using **Terraform**, ensuring consistent, automated, and scalable provisioning of resources.
- **Backend**: Python-based backend with robust endpoints for query processing. The system includes four main APIs, all built resorting to FastAPI:
- **Authentication API**: Manages secure user authentication and token handling, which supports JWT encoding and decoding with robust encryption algorithms.
- **Conversations API**: Facilitates the interaction flow by managing user sessions, storing and load conversation history, delete a previous conversation or all of them .
- **Users API**: Handles user-related operations such as profile updates, and subscriptions management.
- **RAG API**: This acts like an interface between the user and the whole backend.(Specialized for managing and processing the retrieval-augmented generation (RAG) workflows, such as receiving a query from an user and)
- **Database**: DynamoDB hosted on AWS, designed for scalability and real-time updates.
- **Data Collection**: The team implemented a daily routine that scrapes and monitors legislative sources for updates, ensuring the database contains the most current laws.
- **Query Enhancement**:
    - **Input Classification Framework**: Proprietary classification model trained using **spaCy** to map user queries to the relevant codes of Portuguese legislation. The training dataset included diverse questions and contextual information from the portuguese law corpus ensuring a robust representation. The model has a two-stage classification approach, incorporating keyword-based confidence adjustment and similarity-based confirmation to enhance accuracy.
    - **Query Expansion**: Techniques are applied to enrich user queries with context for improved retrieval.
    - **Metadata Extraction**: Key details (legislation date, question date, summary, subject and region) are extracted to refine the search.
    
    
- **Response Generation**:
    
    **Why RAG?**
    
    Training a model on the legislation corpus is basically impractical due to the high costs and complexity. Instead, RAG allows us to maintain a continuously updated database based only on Portuguese Legislation, ensuring that responses are always based on the latest legal information. This approach minimizes errors and hallucinations by grounding the generative AI's outputs in reliable and retrieved data. You can see the steps made by RAG below and on the flow diagram. 
    
    - For the vector database, we use Pinecone. This vectorDB is available via AWS which enhances its availability for cloud-native applications, which is our case.
    - For the Embedding process we use a hybrid approach between Dense Embeddings and Sparse Embeddings. Dense Embeddings capture the semantic meaning of the text in a compact form, and Sparse Embeddings are useful for handling rare or domain-specific terms , which Dense might overlook. The hybrid query mechanism scales the contributions of dense and sparse vectors using an adjustable parameter (`alpha`)
    - For the validation and reranking of the retrieved documents, we apply two methods and combine the results.
        
        We rank the retrieved information using BM250, this uses a Term Frequency; Inverse Document Frequency algorithm in order to find keywords in the document that are present in the query.
        
        We also use a LLM in order to rerank the retrieved documents based on the query.
        
        If the overall score for relevancy is under 80 we don’t use it as context.
        
    - For prompt engineering, we use *DSPy*. It is a framework for algorithmically optimizing the prompts and weights of a Large Language Model, where we can use prompt techniques, like *ChainOfThought*, based on the query provided by the user. This framework is particularly effective for creating complex pipelines that involve multiple interactions with the LLM.
    
    
- **Output**: The processed query and relevant legal response are returned to the user, with adequate links that shows where the information given comes from, validating that is real and true.
- **OCR**: LegislAI has the capability to accepts documents in PDF or image format. In the PDF processing module, each page is converted into an image, and text is extracted using OCR (via Tesseract). For image processing, the team developed algorithms to process skewing in images , contrast enhancement, and noise reduction to improve text readability. Both processes output the extracted text in a standardized JSON format, organized by pages and paragraphs, ensuring seamless integration with the chatbot.


- **Front end:** The front end was developed using Next.js due to its efficient approach to building web applications. For managing global authentication state, we implemented React Redux, while Framer Motion was utilized for animations within the application.

## 4. Design and Implementation

**Flow Diagram**:

The following diagram represents the application flow:

**Authentication:**

If the user does not have an account, they need to create one with a valid email, username and password. If the user has an account, they just log in. 

After log in, based on the subscription plan, the user enters a query or a query and a document. 

**Processing a Query (Without a Document)**:

If the user only submits a query, it is processed by the Query Enhancement Module, which returns a dictionary containing metadata extracted from the query (summary, legislation date, question date, subject, and region ), expanded queries variations and a code classifier. Next, it is time to get the retrieved contexts from the Legislation Database. Finally, the query and retrieved contexts are refined using prompt techniques and returns the final answer to the user.

**Processing a Query with a Document**:

If the user provides both a query and a document, the OCR Module is activated. This module processes the uploaded file, applies prompt techniques and returns the answer to the user.


The diagram represents the various interactions that users can have with the LegisAI system. All users are able to authenticate themselves, and all users can input queries. However, only advanced users (*Utilizador Avançado*) can input files to the system to be analyzed.

The system itself also interacts with various components:

- The Daily Scraper runs to keep the database updated.
- The OCR Interpreter collects and analyzes any files provided by the user.
- The RAG component works on the user's query to pass it to the LLM in the best way.
- The LLM then generates the final response to the user's query.

The diagram provides a visual representation of these interactions and the various components involved in the LegisAI system.


## 5. Challenges and Limitations

- **Challenges**:
    - Handling ambiguous queries,
    - Real-time updates for new laws,
    - Non existing API to retrieve the information from the sources
    - Understanding the Portuguese law and how it is organized
    - Some law branches are extremely argumentative/prone to interpretation
- **Limitations:**
    - Given that the team is using quantized models through free providers, the answers could be a lot more refined if another approaches were used.

## 6. Future Work

- Adding support for multiple languages.
- Expand to all the legislation.
- Expand to include jurisprudence, allowing users to select a specific court and ask questions customized to that court's rulings.
- Retrieve revoked laws from Diário da Republica

  
## **7. Installation**

### **Prerequisites**
- [Python](https://www.python.org/)
- [Pyenv](https://github.com/pyenv/pyenv)
- [Pyenv Virtual Environment](https://github.com/pyenv/pyenv-virtualenv)
- [Docker](https://www.docker.com/)

---

### **Setup Instructions**

1. Clone the repository and navigate to the `legislai-be` directory:
    ```bash
    git clone <repo-url>
    cd legislai-be
    ```

2. Install project dependencies:
    ```bash
    make setup
    ```

3. Create a `.env` file:
    ```bash
    cp .env.example .env
    ```
---

### **API Endpoints**

#### **Authentication API**
| Method | Endpoint                  | Description          |
|--------|---------------------------|----------------------|
| POST   | `/auth/register`          | Register a user      |
| POST   | `/auth/login`             | Log in a user        |
| POST   | `/auth/logout`            | Log out a user       |
| POST   | `/auth/refresh-tokens`    | Refresh tokens       |

#### **Users API**
| Method | Endpoint         | Description          |
|--------|------------------|----------------------|
| GET    | `/users/`        | Get user information |
| PATCH  | `/users/`        | Update user profile  |
| GET    | `/users/plan/`   | Get user plan        |
| PATCH  | `/users/plan/`   | Update user plan     |

#### **Conversations API**
| Method | Endpoint                                   | Description                  |
|--------|-------------------------------------------|------------------------------|
| POST   | `/conversations/new_conversation`         | Create a new conversation    |
| DELETE | `/conversations/{conversation_id}/delete` | Delete a conversation        |
| GET    | `/conversations/load_last_conversations`  | Get recent conversations     |

#### **RAG API**
| Method | Endpoint      | Description        |
|--------|---------------|--------------------|
| POST   | `/rag/query`  | Process user query |

---
