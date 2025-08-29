from __future__ import annotations
import os
import json
from typing import Dict, List, Any, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


class GoogleFormsCreator:
    """
    A class to create Google Forms automatically from JSON configuration files.
    """
    
    def __init__(self, client_secrets_file: str = "client_secrets.json", 
                 token_file: str = "token.json"):
        self.SCOPES = ["https://www.googleapis.com/auth/forms.body"]
        self.DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
        self.client_secrets_file = client_secrets_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self) -> None:
        """Handle Google API authentication."""
        creds = self._get_credentials()
        self.service = build("forms", "v1", credentials=creds,
                           discoveryServiceUrl=self.DISCOVERY_DOC, 
                           static_discovery=False)
    
    def _get_credentials(self) -> Credentials:
        """Get or refresh Google API credentials."""
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_file, "w") as f:
                f.write(creds.to_json())
        
        return creds
    
    def create_form_from_json(self, json_file_path: str) -> Dict[str, Any]:
        """
        Create a Google Form from a JSON configuration file.
        
        Args:
            json_file_path: Path to the JSON file containing form configuration
            
        Returns:
            Dictionary containing form_id and responder_uri
        """
        with open(json_file_path, 'r', encoding='utf-8') as f:
            form_config = json.load(f)
        
        return self.create_form_from_config(form_config)
    
    def create_form_from_config(self, form_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Google Form from a configuration dictionary.
        
        Args:
            form_config: Dictionary containing form configuration
            
        Returns:
            Dictionary containing form_id and responder_uri
        """
        # Create blank form
        form_info = form_config.get("form_info", {"title": "API-created form"})
        new_form = {"info": form_info}
        
        created = self.service.forms().create(body=new_form).execute()
        form_id = created["formId"]
        
        # Add questions
        questions = form_config.get("questions", [])
        if questions:
            self._add_questions_to_form(form_id, questions)
        
        # Get form details
        form = self.service.forms().get(formId=form_id).execute()
        
        return {
            "form_id": form_id,
            "responder_uri": form.get("responderUri"),
            "edit_uri": f"https://docs.google.com/forms/d/{form_id}/edit"
        }
    
    def _add_questions_to_form(self, form_id: str, questions: List[Dict[str, Any]]) -> None:
        """Add multiple questions to a form."""
        requests = []
        
        for index, question_config in enumerate(questions):
            request = self._create_question_request(question_config, index)
            requests.append(request)
        
        if requests:
            batch_update_body = {"requests": requests}
            self.service.forms().batchUpdate(
                formId=form_id, body=batch_update_body).execute()
    
    def _create_question_request(self, question_config: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Create a question request based on question type."""
        question_type = question_config.get("type", "RADIO").upper()
        
        if question_type in ["RADIO", "CHECKBOX"]:
            return self._create_choice_question(question_config, index)
        elif question_type == "TEXT":
            return self._create_text_question(question_config, index)
        elif question_type == "PARAGRAPH_TEXT":
            return self._create_paragraph_question(question_config, index)
        elif question_type == "SCALE":
            return self._create_scale_question(question_config, index)
        else:
            raise ValueError(f"Unsupported question type: {question_type}")
    
    def _create_choice_question(self, config: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Create a multiple choice or checkbox question."""
        options = [{"value": option} for option in config.get("options", [])]
        
        return {
            "createItem": {
                "item": {
                    "title": config.get("title", "Untitled Question"),
                    "description": config.get("description", ""),
                    "questionItem": {
                        "question": {
                            "required": config.get("required", False),
                            "choiceQuestion": {
                                "type": config.get("type", "RADIO").upper(),
                                "options": options,
                                "shuffle": config.get("shuffle", False)
                            }
                        }
                    }
                },
                "location": {"index": index}
            }
        }
    
    def _create_text_question(self, config: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Create a short text question."""
        return {
            "createItem": {
                "item": {
                    "title": config.get("title", "Untitled Question"),
                    "description": config.get("description", ""),
                    "questionItem": {
                        "question": {
                            "required": config.get("required", False),
                            "textQuestion": {
                                "paragraph": False
                            }
                        }
                    }
                },
                "location": {"index": index}
            }
        }
    
    def _create_paragraph_question(self, config: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Create a paragraph text question."""
        return {
            "createItem": {
                "item": {
                    "title": config.get("title", "Untitled Question"),
                    "description": config.get("description", ""),
                    "questionItem": {
                        "question": {
                            "required": config.get("required", False),
                            "textQuestion": {
                                "paragraph": True
                            }
                        }
                    }
                },
                "location": {"index": index}
            }
        }
    
    def _create_scale_question(self, config: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Create a linear scale question."""
        return {
            "createItem": {
                "item": {
                    "title": config.get("title", "Untitled Question"),
                    "description": config.get("description", ""),
                    "questionItem": {
                        "question": {
                            "required": config.get("required", False),
                            "scaleQuestion": {
                                "low": config.get("low", 1),
                                "high": config.get("high", 5),
                                "lowLabel": config.get("low_label", ""),
                                "highLabel": config.get("high_label", "")
                            }
                        }
                    }
                },
                "location": {"index": index}
            }
        }


# Example usage
def main():
    """Example of how to use the GoogleFormsCreator class."""
    creator = GoogleFormsCreator()
    
    # Create form from JSON file
    try:
        result = creator.create_form_from_json("form_config.json")
        print("Form created successfully!")
        print(f"Form ID: {result['form_id']}")
        print(f"Responder URL: {result['responder_uri']}")
        print(f"Edit URL: {result['edit_uri']}")
    except FileNotFoundError:
        print("form_config.json not found. Creating a sample form instead...")
        
        # Create form from dictionary
        sample_config = {
            "form_info": {
                "title": "Sample Survey",
                "description": "This is a sample survey created via API"
            },
            "questions": [
                {
                    "type": "RADIO",
                    "title": "In what year did the United States land on the moon?",
                    "options": ["1965", "1967", "1969", "1971"],
                    "required": True,
                    "shuffle": True
                },
                {
                    "type": "TEXT",
                    "title": "What is your name?",
                    "required": True
                },
                {
                    "type": "SCALE",
                    "title": "How satisfied are you with this service?",
                    "low": 1,
                    "high": 5,
                    "low_label": "Very Dissatisfied",
                    "high_label": "Very Satisfied",
                    "required": True
                }
            ]
        }
        
        result = creator.create_form_from_config(sample_config)
        print("Sample form created successfully!")
        print(f"Form ID: {result['form_id']}")
        print(f"Responder URL: {result['responder_uri']}")
        print(f"Edit URL: {result['edit_uri']}")


if __name__ == "__main__":
    main()