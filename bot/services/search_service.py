import os
import logging
import asyncio
import openai

from bot.config.tokens import OPENAI_API_KEY
from bot.config.gpt_prompt import PROMPT


# Disable HuggingFace tokenizers parallelism warnings
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

logger = logging.getLogger(__name__)
openai.api_key = OPENAI_API_KEY


async def ask_gpt(user_query: str) -> str:
    """
    Отправляет запрос в OpenAI и возвращает ответ.
    Таймаут по умолчанию 30 секунд.
    """
    try:
        logger.info("Sending request to OpenAI: %s", user_query)
        loop = asyncio.get_running_loop()
        # run OpenAI call in executor with a timeout
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": PROMPT},
                        {"role": "user", "content": user_query}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
            ),
            timeout=30.0
        )
        answer: str = response.choices[0].message.content.strip()
        logger.info("Received OpenAI response: %s", answer)
        return answer
    except asyncio.TimeoutError:
        logger.error("OpenAI request timed out for query: %s", user_query)
        return "Превышено время ожидания ответа. Попробуйте позже."
    except Exception as e:
        logger.exception("Error calling OpenAI API: %s", e)
        return "Произошла ошибка при обработке запроса. Попробуйте позже."
