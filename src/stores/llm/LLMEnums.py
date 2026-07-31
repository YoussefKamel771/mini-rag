from enum import Enum

class LLMType(str, Enum):
    OPENAI = "openai"
    COHERE = "cohere"

class OpenAIEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"