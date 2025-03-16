from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatResponse(BaseModel):
    message: str = Field(..., description="Generated response from the chatbot")
    sources: List[str] = Field(default_factory=list, description="Source documents used for the response")
    confidence_score: float = Field(..., description="Confidence score of the response")
    sentiment: Optional[str] = Field(None, description="Sentiment analysis of the response")
    
class ChatHistory(BaseModel):
    user_id: int
    messages: List[ChatMessage]
    context: dict = Field(default_factory=dict)
    
class StreamResponse(BaseModel):
    content: str
    done: bool
