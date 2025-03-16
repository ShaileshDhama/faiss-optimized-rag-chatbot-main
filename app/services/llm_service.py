import aiohttp
import json
from typing import AsyncGenerator, List, Optional
from app.core.config import get_settings
from loguru import logger
from app.models.chat import StreamResponse

settings = get_settings()

class LLMService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.MODEL_NAME

    async def generate_response(
        self,
        prompt: str,
        context: List[str],
        stream: bool = False
    ) -> AsyncGenerator[StreamResponse, None]:
        """Generate a response from the LLM with context"""
        
        # Construct system message with context
        system_message = (
            "You are an AI financial advisor. Use the following context to answer the question. "
            "If you're not sure about something, say so. Always maintain professionalism and accuracy.\n\n"
            "Context:\n" + "\n".join(context)
        )

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": stream
                }
            ) as response:
                if stream:
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line)
                                if "error" in data:
                                    logger.error(f"Error from LLM: {data['error']}")
                                    yield StreamResponse(
                                        content=f"Error: {data['error']}",
                                        done=True
                                    )
                                    return
                                
                                content = data.get("message", {}).get("content", "")
                                done = data.get("done", False)
                                
                                yield StreamResponse(
                                    content=content,
                                    done=done
                                )
                            except json.JSONDecodeError as e:
                                logger.error(f"Error decoding JSON: {e}")
                                continue
                else:
                    data = await response.json()
                    if "error" in data:
                        logger.error(f"Error from LLM: {data['error']}")
                        yield StreamResponse(
                            content=f"Error: {data['error']}",
                            done=True
                        )
                        return
                    
                    content = data.get("message", {}).get("content", "")
                    yield StreamResponse(
                        content=content,
                        done=True
                    )

    async def analyze_sentiment(self, text: str) -> Optional[str]:
        """Analyze the sentiment of a given text"""
        prompt = f"Analyze the sentiment of this text and respond with exactly one word (positive/neutral/negative): {text}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}]
                }
            ) as response:
                data = await response.json()
                sentiment = data.get("message", {}).get("content", "").strip().lower()
                
                if sentiment in ["positive", "neutral", "negative"]:
                    return sentiment
                return None
