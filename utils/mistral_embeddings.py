from typing import List
from mistralai.client import MistralClient
from mistralai.models.embeddings import EmbeddingResponse
from utils.env_loader import get_api_key
import numpy as np
import logging

logger = logging.getLogger(__name__)

class MistralEmbeddings:
    """
    Класс для работы с эмбеддингами Mistral AI
    """
    
    def __init__(self, model: str = "mistral-embed"):
        """
        Инициализация клиента Mistral
        
        Args:
            model (str): Название модели для эмбеддингов
        """
        self.api_key = get_api_key('mistral')
        self.client = MistralClient(api_key=self.api_key)
        self.model = model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Получение эмбеддингов для списка текстов
        
        Args:
            texts (List[str]): Список текстов для эмбеддинга
            
        Returns:
            List[List[float]]: Список векторов эмбеддинг��в
        """
        try:
            embeddings: List[List[float]] = []
            
            for text in texts:
                response: EmbeddingResponse = self.client.embeddings(
                    model=self.model,
                    input=[text]
                )
                embeddings.append(response.data[0].embedding)
            
            logger.info(f"Успешно получены эмбеддинги для {len(texts)} текстов")
            return embeddings
            
        except Exception as e:
            logger.error(f"Ошибка при получении эмбеддингов: {str(e)}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """
        Получение эмбеддинга для одного текста
        
        Args:
            text (str): Текст для эмбеддинга
            
        Returns:
            List[float]: Вектор эмбеддинга
        """
        try:
            response: EmbeddingResponse = self.client.embeddings(
                model=self.model,
                input=[text]
            )
            
            logger.info("Успешно получен эмбеддинг для запроса")
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Ошибка при получении эмбеддинга: {str(e)}")
            raise
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Вычисление косинусного сходства между двумя эмбеддингами
        
        Args:
            embedding1 (List[float]): Первый вектор эмбеддинга
            embedding2 (List[float]): Второй вектор эмбеддинга
            
        Returns:
            float: Значение косинусного сходства
        """
        return np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )

def main():
    """
    Пример использования класса MistralEmbeddings
    """
    try:
        embeddings = MistralEmbeddings()
        
        # Пример текстов
        texts = [
            "The quick brown fox",
            "jumps over the lazy dog"
        ]
        
        # Получение эмбеддингов
        document_embeddings = embeddings.embed_documents(texts)
        query_embedding = embeddings.embed_query("fox jumps")
        
        # Выч��сление сходства
        similarity = embeddings.similarity(
            document_embeddings[0],
            query_embedding
        )
        
        print(f"Косинусное сходство: {similarity}")
        
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    main() 