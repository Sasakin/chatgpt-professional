from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from utils.env_loader import get_api_key
import tiktoken
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_gpt_response_and_token_count(user_input: str) -> tuple[str, int]:
    """
    Получает ответ от Mistral API и подсчитывает количество токенов
    
    Args:
        user_input (str): Входной текст пользователя
        
    Returns:
        tuple[str, int]: (ответ модели, количество токенов)
        
    Raises:
        Exception: При ошибке подключения к API или обработки ответа
    """
    try:
        # Получаем API ключ и инициализируем клиент
        api_key = get_api_key('mistral')
        client = MistralClient(api_key=api_key)
        
        # Создаем сообщение
        messages = [
            ChatMessage(
                role="user",
                content=user_input
            )
        ]
        
        # Получаем ответ от API
        response = client.chat(
            model="mistral-small",
            messages=messages
        )
        
        # Получаем текст ответа
        response_text = response.messages[0].content
        
        # Подсчет токенов
        encoding = tiktoken.get_encoding("cl100k_base")
        input_tokens = len(encoding.encode(user_input))
        output_tokens = len(encoding.encode(response_text))
        total_tokens = input_tokens + output_tokens
        
        logger.info(f"Успешно получен ответ. Токенов: {total_tokens}")
        return response_text, total_tokens
        
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}")
        raise

def main():
    """
    Пример использования функции подсчета токенов
    """
    try:
        user_input = "Who is the best French painter? Answer in one short sentence."
        response, token_count = get_gpt_response_and_token_count(user_input)
        
        print("Ответ Mistral:", response)
        print("Количество токенов:", token_count)
        
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    main() 