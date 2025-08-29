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
    Enhanced with quiz features, feedback, and image support.
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
        # Create blank form with only title (API limitation)
        form_info = form_config.get("form_info", {"title": "API-created form"})
        new_form = {"info": {"title": form_info.get("title", "API-created form")}}
        
        created = self.service.forms().create(body=new_form).execute()
        form_id = created["formId"]
        
        # Update form with description and settings using batchUpdate
        requests = []
        
        # Add description if provided
        if form_info.get("description"):
            requests.append({
                "updateFormInfo": {
                    "info": {
                        "title": form_info.get("title", "API-created form"),
                        "description": form_info.get("description", "")
                    },
                    "updateMask": "description"
                }
            })
        
        # Set up as quiz if specified
        is_quiz = form_config.get("is_quiz", True)
        if is_quiz:
            quiz_settings = form_config.get("quiz_settings", {})
            requests.append({
                "updateSettings": {
                    "settings": {
                        "quizSettings": {
                            "isQuiz": True
                        }
                    },
                    "updateMask": "quizSettings.isQuiz"
                }
            })
        
        # Execute initial updates
        if requests:
            batch_update_body = {"requests": requests}
            self.service.forms().batchUpdate(formId=form_id, body=batch_update_body).execute()
        
        # Add questions
        questions = form_config.get("questions", [])
        if questions:
            self._add_questions_to_form(form_id, questions, is_quiz)
        
        # Get form details
        form = self.service.forms().get(formId=form_id).execute()
        
        return {
            "form_id": form_id,
            "responder_uri": form.get("responderUri"),
            "edit_uri": f"https://docs.google.com/forms/d/{form_id}/edit"
        }
    
    def _add_questions_to_form(self, form_id: str, questions: List[Dict[str, Any]], is_quiz: bool = False) -> None:
        """Add multiple questions to a form."""
        requests = []
        
        for index, question_config in enumerate(questions):
            request = self._create_question_request(question_config, index, is_quiz)
            requests.append(request)
        
        if requests:
            batch_update_body = {"requests": requests}
            self.service.forms().batchUpdate(formId=form_id, body=batch_update_body).execute()
    
    def _create_question_request(self, question_config: Dict[str, Any], index: int, is_quiz: bool = False) -> Dict[str, Any]:
        """Create a question request based on question type."""
        question_type = question_config.get("type", "RADIO").upper()
        
        if question_type in ["RADIO", "CHECKBOX"]:
            return self._create_choice_question(question_config, index, is_quiz)
        elif question_type == "TEXT":
            return self._create_text_question(question_config, index, is_quiz)
        elif question_type == "PARAGRAPH_TEXT":
            return self._create_paragraph_question(question_config, index, is_quiz)
        elif question_type == "SCALE":
            return self._create_scale_question(question_config, index, is_quiz)
        elif question_type == "IMAGE":
            return self._create_image_question(question_config, index, is_quiz)
        else:
            raise ValueError(f"Unsupported question type: {question_type}")
    
    def _create_choice_question(self, config: Dict[str, Any], index: int, is_quiz: bool = False) -> Dict[str, Any]:
        """Create a multiple choice or checkbox question."""
        options = []
        correct_answers = config.get("correct_answers", [])
        
        for i, option in enumerate(config.get("options", [])):
            option_obj = {"value": option}
            # Don't add isCorrect field - handle this in grading section
            options.append(option_obj)
        
        question_item = {
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
        }
        
        # Add quiz grading if this is a quiz question
        if is_quiz and correct_answers:
            points = config.get("points", 1)
            grading = {
                "pointValue": points,
                "correctAnswers": {
                    "answers": [{"value": answer} for answer in correct_answers]
                }
            }
            
            # Add feedback (no general feedback for auto-graded questions)
            feedback = config.get("feedback", {})
            if feedback.get("correct"):
                grading["whenRight"] = {
                    "text": feedback.get("correct", "Correct!")
                }
                
            if feedback.get("incorrect"):
                grading["whenWrong"] = {
                    "text": feedback.get("incorrect", "Incorrect. Please review the material.")
                }
            
            question_item["questionItem"]["question"]["grading"] = grading
        
        # Add image if provided and valid
        image_url = config.get("image_url")
        if image_url and image_url != "https://example.com/code-snippet.png" and not image_url.startswith("https://example.com"):
            question_item["questionItem"]["image"] = {
                "sourceUri": image_url
            }
        
        return {
            "createItem": {
                "item": question_item,
                "location": {"index": index}
            }
        }
    
    def _create_text_question(self, config: Dict[str, Any], index: int, is_quiz: bool = False) -> Dict[str, Any]:
        """Create a short text question."""
        question_item = {
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
        }
        
        # Add quiz grading for text questions if needed
        if is_quiz and config.get("correct_answers"):
            points = config.get("points", 1)
            grading = {
                "pointValue": points,
                "correctAnswers": {
                    "answers": [{"value": answer} for answer in config.get("correct_answers", [])]
                }
            }
            
            # Add feedback for text questions (can have general feedback since they're not auto-graded)
            feedback = config.get("feedback", {})
            if feedback.get("general"):
                grading["generalFeedback"] = {
                    "text": feedback.get("general", "")
                }
            
            question_item["questionItem"]["question"]["grading"] = grading
        elif is_quiz and config.get("points", 0) > 0:
            # For text questions without correct answers but with points
            question_item["questionItem"]["question"]["grading"] = {
                "pointValue": config.get("points", 1)
            }
            
            feedback = config.get("feedback", {})
            if feedback.get("general"):
                question_item["questionItem"]["question"]["grading"]["generalFeedback"] = {
                    "text": feedback.get("general", "")
                }
        
        # Add image if provided and valid
        image_url = config.get("image_url")
        if image_url and image_url != "https://example.com/code-snippet.png" and not image_url.startswith("https://example.com"):
            question_item["questionItem"]["image"] = {
                "sourceUri": image_url
            }
        
        return {
            "createItem": {
                "item": question_item,
                "location": {"index": index}
            }
        }
    
    def _create_paragraph_question(self, config: Dict[str, Any], index: int, is_quiz: bool = False) -> Dict[str, Any]:
        """Create a paragraph text question."""
        question_item = {
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
        }
        
        # Add quiz grading for paragraph questions if needed
        if is_quiz and config.get("points", 0) > 0:
            points = config.get("points", 1)
            grading = {
                "pointValue": points
            }
            
            # Add feedback for manual grading
            feedback = config.get("feedback", {})
            if feedback.get("general"):
                grading["generalFeedback"] = {
                    "text": feedback.get("general", "This question will be manually graded.")
                }
            
            question_item["questionItem"]["question"]["grading"] = grading
        
        # Add image if provided and valid
        image_url = config.get("image_url")
        if image_url and image_url != "https://example.com/code-snippet.png" and not image_url.startswith("https://example.com"):
            question_item["questionItem"]["image"] = {
                "sourceUri": image_url
            }
        
        return {
            "createItem": {
                "item": question_item,
                "location": {"index": index}
            }
        }
    
    def _create_scale_question(self, config: Dict[str, Any], index: int, is_quiz: bool = False) -> Dict[str, Any]:
        """Create a linear scale question."""
        question_item = {
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
        }
        
        # Add quiz grading for scale questions if needed
        if is_quiz and config.get("correct_answer"):
            points = config.get("points", 1)
            grading = {
                "pointValue": points,
                "correctAnswers": {
                    "answers": [{"value": str(config.get("correct_answer"))}]
                }
            }
            question_item["questionItem"]["question"]["grading"] = grading
        elif is_quiz and config.get("points", 0) > 0:
            # For scale questions with points but no correct answer
            question_item["questionItem"]["question"]["grading"] = {
                "pointValue": config.get("points", 1)
            }
        
        # Add image if provided and valid
        image_url = config.get("image_url")
        if image_url and image_url != "https://example.com/code-snippet.png" and not image_url.startswith("https://example.com"):
            question_item["questionItem"]["image"] = {
                "sourceUri": image_url
            }
        
        return {
            "createItem": {
                "item": question_item,
                "location": {"index": index}
            }
        }
    
    def _create_image_question(self, config: Dict[str, Any], index: int, is_quiz: bool = False) -> Dict[str, Any]:
        """Create an image-based question."""
        options = []
        correct_answers = config.get("correct_answers", [])
        
        for option in config.get("options", []):
            option_obj = {"value": option}
            # Don't add isCorrect field - handle this in grading section
            options.append(option_obj)
        
        question_item = {
            "title": config.get("title", "Untitled Question"),
            "description": config.get("description", ""),
            "questionItem": {
                "question": {
                    "required": config.get("required", False),
                    "choiceQuestion": {
                        "type": "RADIO",  # Image questions are typically radio buttons
                        "options": options,
                        "shuffle": config.get("shuffle", False)
                    }
                }
            }
        }
        
        # Add image - moved to questionItem level for image-based questions
        image_url = config.get("image_url")
        if image_url and image_url != "https://example.com/code-snippet.png" and not image_url.startswith("https://example.com"):
            question_item["questionItem"]["image"] = {
                "sourceUri": image_url
            }
        elif image_url and (image_url == "https://example.com/code-snippet.png" or image_url.startswith("https://example.com")):
            # Skip image for placeholder URLs and add note to description
            current_desc = question_item.get("description", "")
            question_item["description"] = f"{current_desc}\n[Note: Image placeholder removed - please add a valid image URL]".strip()
        
        # Add quiz grading
        if is_quiz and correct_answers:
            points = config.get("points", 1)
            grading = {
                "pointValue": points,
                "correctAnswers": {
                    "answers": [{"value": answer} for answer in correct_answers]
                }
            }
            
            # Add feedback (no general feedback for auto-graded questions)
            feedback = config.get("feedback", {})
            if feedback.get("correct"):
                grading["whenRight"] = {
                    "text": feedback.get("correct", "Correct!")
                }
                
            if feedback.get("incorrect"):
                grading["whenWrong"] = {
                    "text": feedback.get("incorrect", "Incorrect.")
                }
            
            question_item["questionItem"]["question"]["grading"] = grading
        
        return {
            "createItem": {
                "item": question_item,
                "location": {"index": index}
            }
        }