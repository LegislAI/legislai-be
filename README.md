# **LegisAI Backend**

## **1. Project Overview**

- **Main Goal**: Simplify the search and understanding of Portuguese legislation by providing an AI-powered virtual assistant accessible through a centralized website.
- **Problem Statement**: Navigating Portuguese legislation is complex and often inaccessible without specialized knowledge. LegisAI aims to resolve this by offering an intuitive, centralized, and AI-enhanced legal database, empowering individuals to understand and utilize legal information effectively.

---

## **2. Context and Background**

Portuguese legislation is dense and challenging to navigate, making it difficult for individuals to understand their rights and obligations. **LegisAI** addresses this by automating searches, contextualizing results, and simplifying access to up-to-date legal information.

Key challenges include:
- The ever-changing nature of legislation.
- Accessibility issues for non-experts.
- The complexity of retrieving and interpreting legal information.

LegisAI provides a centralized and user-friendly solution, acting as an AI-powered legal database.

---

## **3. Technical Details**

### **Backend Overview**
The backend is implemented using Python and FastAPI, with the following key components:

#### **1. Authentication API**
- Manages secure user authentication.
- Utilizes JWT for token encoding/decoding with robust encryption.

#### **2. Conversations API**
- Facilitates interaction flow.
- Handles user sessions, conversation storage, and retrieval.

#### **3. Users API**
- Manages user profiles and subscription plans.

#### **4. RAG API**
- Interface for Retrieval-Augmented Generation (RAG) workflows.
- Processes user queries and integrates the entire backend pipeline.

---

### **Infrastructure**
- **Deployment**: Managed using **Terraform**, chosen for scalability and team collaboration.
- **Database**: **DynamoDB** hosted on AWS, optimized for real-time updates.
- **Vector Database**: **Pinecone**, utilizing a hybrid(Dense + Sparse) embedding approach for enhanced retrieval accuracy.

---

### **Query Enhancement**
1. **Input Classification**: 
   - Built using **spaCy**, trained on Portuguese law corpora.
   - Two-stage classification approach for keyword-based confidence adjustment and similarity-based validation.

2. **Query Expansion**: Enriches user input for improved context retrieval.

3. **Metadata Extraction**: Extracts key details like legislation date, query date, and subject.

---

### **Response Generation**
- **Why RAG?**
  - Ensures responses are based on current and reliable legislative data.
  - Minimizes hallucinations from the generative AI by grounding results in retrieved information.

- **Prompt Engineering**:
  - Utilizes **DSPy** for optimizing LLM prompts.
  - Techniques like *ChainOfThought* refine response accuracy.


---

### **OCR Integration**
- **PDF & Image Support**:
  - **PDFs**: Pages are converted to images, and text is extracted using Tesseract.
  - **Images**: Specialized OCR model with preprocessing (e.g., binarization, contrast enhancement).
  - Outputs structured JSON with text organized by pages and paragraphs.

---

## **4. Installation**

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
