---

# 📋 Google Forms Creator (Python)

Automatically create **Google Forms** (with quiz support, feedback, and images) using Python and the **Google Forms API**.

---

## 🚀 Features

* 🔑 Google OAuth2 Authentication
* 📝 Create Forms from **JSON configuration**
* 🎯 Quiz Support (auto-grading, points, feedback)
* 🖼️ Add Images to Questions
* 📊 Multiple Question Types:

  * Multiple Choice (Radio / Checkbox)
  * Short Answer / Paragraph
  * Linear Scale
  * Image-based Questions

---

## 📂 Project Structure

```
.
├── google_forms_creator.py   # Core class implementation
├── client_secrets.json       # OAuth2 credentials
├── token.json                # Stored access token
├── sample_form.json          # Example form config
└── README.md                 # Documentation
```

---

## ⚡ Setup Instructions

### 1. Enable Google Forms API

* Go to [Google Cloud Console](https://console.cloud.google.com/)
* Create a project & enable **Forms API**
* Download `client_secrets.json` and place it in project root

### 2. Install Dependencies

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 3. Authentication

First run will open a browser to authenticate with Google. Token is saved in `token.json` for reuse.

---

## 🛠️ Usage

### Create Form from JSON

```python
from google_forms_creator import GoogleFormsCreator

creator = GoogleFormsCreator()

result = creator.create_form_from_json("sample_form.json")
print("Form created!")
print("Form ID:", result["form_id"])
print("Edit URL:", result["edit_uri"])
print("Responder URL:", result["responder_uri"])
```

---

## 📑 Example JSON Config

```json
{
  "form_info": {
    "title": "Test One - Python & Linux Fundamentals",
    "description": "Week One Topics Test - Python, Linux, and Git"
  },
  "is_quiz": true,
  "quiz_settings": {
    "release_score": "IMMEDIATELY"
  },
  "questions": [
    {
      "title": "Which command lists files in Linux?",
      "type": "RADIO",
      "options": ["ls", "pwd", "cd", "touch"],
      "correct_answers": ["ls"],
      "points": 2,
      "required": true,
      "feedback": {
        "correct": "✅ Correct! 'ls' lists files.",
        "incorrect": "❌ Try again. Hint: It starts with 'l'."
      }
    }
  ]
}
```

---

## 📊 Architecture Diagrams

### 🔑 Authentication Flow

```mermaid
flowchart TD
    A[Start Script] --> B{Token Exists?}
    B -- Yes --> C[Load token.json]
    B -- No --> D[OAuth Consent Screen]
    D --> E[Google Auth Server]
    E --> F[Save token.json]
    C --> G[Authenticated Service]
    F --> G[Authenticated Service]
```

---

### 🏗️ Class Design

```mermaid
classDiagram
    class GoogleFormsCreator {
        -SCOPES : List
        -DISCOVERY_DOC : str
        -client_secrets_file : str
        -token_file : str
        -service : Any
        +__init__()
        +_authenticate()
        +_get_credentials()
        +create_form_from_json()
        +create_form_from_config()
        +_add_questions_to_form()
        +_create_question_request()
        +_create_choice_question()
        +_create_text_question()
        +_create_paragraph_question()
        +_create_scale_question()
        +_create_image_question()
    }
```

---

### ⚙️ Workflow

```mermaid
sequenceDiagram
    participant User
    participant GoogleFormsCreator
    participant GoogleAPI

    User ->> GoogleFormsCreator: create_form_from_json("sample_form.json")
    GoogleFormsCreator ->> GoogleFormsCreator: _get_credentials()
    GoogleFormsCreator ->> GoogleAPI: Create blank form
    GoogleFormsCreator ->> GoogleAPI: batchUpdate (title, desc, quiz)
    GoogleFormsCreator ->> GoogleAPI: Add questions
    GoogleAPI -->> GoogleFormsCreator: Return formId, responderUri
    GoogleFormsCreator -->> User: form_id, edit_uri, responder_uri
```

---

## ✅ Output Example

```bash
Form created!
Form ID: 1FAIpQLSfxxxxxxxxxxxx
Edit URL: https://docs.google.com/forms/d/1FAIpQLSfxxxxxxxxxxxx/edit
Responder URL: https://docs.google.com/forms/d/e/1FAIpQLSfxxxxxxxxxxxx/viewform
```

---

## 🧑‍💻 Author

Built with ❤️ by **Jayanth**

---
