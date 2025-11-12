"""
FastAPI REST API for Python Quiz Chatbot
Provides endpoints for frontend to interact with quiz questions and submit answers.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import random
from chatbot import Question, build_questions, LETTER_KEYS

app = FastAPI(
	title="Python Quiz API",
	description="REST API for Python beginner-level quiz questions",
	version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  # In production, replace with specific frontend URL
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Load questions once at startup
QUESTIONS: List[Question] = build_questions()


# Pydantic Models for Request/Response
class QuestionResponse(BaseModel):
	"""Question response model (without correct answer for security)"""
	id: int
	question_text: str
	options: List[str]

	class Config:
		json_schema_extra = {
			"example": {
				"id": 0,
				"question_text": "What is the correct file extension for Python files?",
				"options": [".pyt", ".pt", ".py", ".python"]
			}
		}


class QuestionDetailResponse(BaseModel):
	"""Question with full details including correct answer (for admin/internal use)"""
	id: int
	question_text: str
	options: List[str]
	correct_option_key: str
	explanation: str

	class Config:
		json_schema_extra = {
			"example": {
				"id": 0,
				"question_text": "What is the correct file extension for Python files?",
				"options": [".pyt", ".pt", ".py", ".python"],
				"correct_option_key": "c",
				"explanation": ".py is the standard extension for Python source files."
			}
		}


class AnswerSubmitRequest(BaseModel):
	"""Request model for submitting an answer"""
	question_id: int = Field(..., ge=0, description="ID of the question (0-indexed)")
	answer: str = Field(..., pattern="^[a-d]$", description="Selected answer: a, b, c, or d")

	class Config:
		json_schema_extra = {
			"example": {
				"question_id": 0,
				"answer": "c"
			}
		}


class AnswerResponse(BaseModel):
	"""Response model after submitting an answer"""
	is_correct: bool
	correct_answer: str
	correct_answer_text: str
	explanation: str

	class Config:
		json_schema_extra = {
			"example": {
				"is_correct": True,
				"correct_answer": "c",
				"correct_answer_text": ".py",
				"explanation": ".py is the standard extension for Python source files."
			}
		}


class StatsResponse(BaseModel):
	"""Statistics about available questions"""
	total_questions: int

	class Config:
		json_schema_extra = {
			"example": {
				"total_questions": 5
			}
		}


class HealthResponse(BaseModel):
	"""Health check response"""
	status: str
	message: str

	class Config:
		json_schema_extra = {
			"example": {
				"status": "healthy",
				"message": "API is running"
			}
		}


# Helper Functions
def question_to_response(question: Question, question_id: int, include_answer: bool = False) -> dict:
	"""Convert Question dataclass to response format"""
	base = {
		"id": question_id,
		"question_text": question.question_text,
		"options": question.options
	}
	if include_answer:
		base.update({
			"correct_option_key": question.correct_option_key,
			"explanation": question.explanation
		})
	return base


# API Endpoints

@app.get("/", tags=["Root"])
async def root():
	"""Root endpoint with API information"""
	return {
		"message": "Python Quiz API",
		"version": "1.0.0",
		"endpoints": {
			"questions": "/api/questions",
			"random_question": "/api/questions/random",
			"submit_answer": "/api/quiz/submit",
			"health": "/api/health",
			"stats": "/api/stats",
			"docs": "/docs"
		}
	}


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
	"""Health check endpoint"""
	return HealthResponse(
		status="healthy",
		message="API is running"
	)


@app.get("/api/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_stats():
	"""Get statistics about available questions"""
	return StatsResponse(total_questions=len(QUESTIONS))


@app.get("/api/questions", response_model=List[QuestionResponse], tags=["Questions"])
async def get_all_questions():
	"""
	Get all quiz questions (without correct answers).
	
	Returns a list of all available questions. The correct answer is not included
	for security reasons - use the submit endpoint to check answers.
	"""
	return [
		QuestionResponse(**question_to_response(q, idx))
		for idx, q in enumerate(QUESTIONS)
	]


@app.get("/api/questions/{question_id}", response_model=QuestionResponse, tags=["Questions"])
async def get_question(question_id: int):
	"""
	Get a specific question by ID (without correct answer).
	
	- **question_id**: Zero-based index of the question (0 to total_questions-1)
	"""
	if question_id < 0 or question_id >= len(QUESTIONS):
		raise HTTPException(
			status_code=404,
			detail=f"Question with ID {question_id} not found. Available IDs: 0-{len(QUESTIONS)-1}"
		)
	return QuestionResponse(**question_to_response(QUESTIONS[question_id], question_id))


@app.get("/api/questions/random", response_model=QuestionResponse, tags=["Questions"])
async def get_random_question():
	"""
	Get a random question (without correct answer).
	
	Useful for presenting questions in random order to users.
	"""
	question_id = random.randint(0, len(QUESTIONS) - 1)
	return QuestionResponse(**question_to_response(QUESTIONS[question_id], question_id))


@app.get("/api/questions/{question_id}/detail", response_model=QuestionDetailResponse, tags=["Questions"])
async def get_question_detail(question_id: int):
	"""
	Get a specific question with full details including correct answer.
	
	⚠️ **Note**: This endpoint includes the correct answer. Use with caution in production.
	Intended for admin/internal use or after answer submission.
	
	- **question_id**: Zero-based index of the question
	"""
	if question_id < 0 or question_id >= len(QUESTIONS):
		raise HTTPException(
			status_code=404,
			detail=f"Question with ID {question_id} not found. Available IDs: 0-{len(QUESTIONS)-1}"
		)
	return QuestionDetailResponse(**question_to_response(QUESTIONS[question_id], question_id, include_answer=True))


@app.post("/api/quiz/submit", response_model=AnswerResponse, tags=["Quiz"])
async def submit_answer(request: AnswerSubmitRequest):
	"""
	Submit an answer for a question and receive feedback.
	
	- **question_id**: ID of the question (0-indexed)
	- **answer**: Selected answer option (a, b, c, or d)
	
	Returns:
	- Whether the answer is correct
	- The correct answer and its text
	- Explanation of the answer
	"""
	if request.question_id < 0 or request.question_id >= len(QUESTIONS):
		raise HTTPException(
			status_code=404,
			detail=f"Question with ID {request.question_id} not found. Available IDs: 0-{len(QUESTIONS)-1}"
		)
	
	question = QUESTIONS[request.question_id]
	is_correct = request.answer.lower() == question.correct_option_key.lower()
	
	# Get the correct answer text
	correct_idx = LETTER_KEYS.index(question.correct_option_key)
	correct_answer_text = question.options[correct_idx]
	
	return AnswerResponse(
		is_correct=is_correct,
		correct_answer=question.correct_option_key,
		correct_answer_text=correct_answer_text,
		explanation=question.explanation
	)


if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=8000)

