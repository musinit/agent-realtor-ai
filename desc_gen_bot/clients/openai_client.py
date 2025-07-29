import os
import base64
from openai import OpenAI
from typing import List, Dict, Any

MODEL_NAME = "gpt-4o-mini"

class OpenAIClient:
    """
    A client for generating property descriptions using the OpenAI API.
    It combines user text, infrastructure data, and images to create a compelling description.
    """

    def __init__(self, api_key: str, prompt_path: str = "prompt.txt"):
        if not api_key:
            raise ValueError("OpenAI API key is required.")
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = self._load_prompt(prompt_path)

    @staticmethod
    def _load_prompt(file_path: str) -> str:
        """Loads the system prompt from a text file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Warning: Prompt file not found at {file_path}. Using a default built-in prompt.")
            return "Ты — опытный риелтор-маркетолог. Твоя задача — создать привлекательное продающее описание для объявления о продаже квартиры. Сначала внимательно проанализируй все входные данные: текст от пользователя, список объектов инфраструктуры и, что особенно важно, фотографии квартиры. Подумай, какие сильные стороны и уникальные особенности можно выделить. На основе этого анализа напиши целостный, яркий и убедительный текст. Ни в коем случае не ври, иначе уволят."
        except Exception as e:
            print(f"Error loading prompt file {file_path}: {e}")
            return "You are a helpful assistant."

    @staticmethod
    def _encode_image_to_base64(image_path: str) -> str:
        """Encodes a single image file to a base64 string."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except FileNotFoundError:
            print(f"Warning: Image file not found at {image_path}. Skipping.")
            return ""
        except Exception as e:
            print(f"Error encoding image {image_path}: {e}")
            return ""

    def _format_infrastructure_prompt(self, summary: Dict[str, List[Dict[str, Any]]]) -> str:
        """Formats the infrastructure dictionary into a human-readable string for the LLM."""
        prompt_parts = ["ИНФРАСТРУКТУРА ПОБЛИЗОСТИ:"]
        if not summary:
            return "Инфраструктура поблизости не найдена."
            
        for category, places in summary.items():
            if places:
                prompt_parts.append(f"\n- {category}:")
                for place in places:
                    name = place.get('name', 'N/A')
                    distance = place.get('distance')
                    prompt_parts.append(f"  - {name} ({distance}м)")
        
        return "\n".join(prompt_parts)

    def create_description(
        self,
        user_prompt: str,
        infrastructure_summary: Dict[str, List[Dict[str, Any]]],
        image_paths: List[str],
        address: str,
    ) -> str:
        """
        Generates a property description by combining text, infrastructure data, and images.
        """
        infrastructure_text = self._format_infrastructure_prompt(infrastructure_summary)
        
        # --- Build the message content ---
        content = [
            {"type": "text", "text": self.system_prompt},
            {"type": "text", "text": f"АДРЕС ОБЪЕКТА: {address}"},
            {"type": "text", "text": "ДЕТАЛИ ОТ ПОЛЬЗОВАТЕЛЯ:\n" + user_prompt},
            {"type": "text", "text": infrastructure_text},
            {"type": "text", "text": "\nТВОЕ ОПИСАНИЕ:"}
        ]

        # --- Add images ---
        for image_path in image_paths:
            base64_image = self._encode_image_to_base64(image_path)
            if base64_image:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                })

        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{
                    "role": "user",
                    "content": content
                }],
                max_tokens=15000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"An error occurred with the OpenAI API: {e}")
            return f"Error: Could not generate description. {e}"

    # # For this real test, we need both API keys
    # OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    # TWOGIS_API_KEY = os.environ.get("TWOGIS_API_KEY")

    # if not OPENAI_API_KEY or not TWOGIS_API_KEY:
    #     print("Please set both OPENAI_API_KEY and TWOGIS_API_KEY environment variables to run this example.")
    #     os._exit(1)
    # else:
    #     # --- Real Data for Demonstration ---
    #     # You can change this address to test different locations
    #     real_address = "Москва, Мосфильмовская ул., 88"
    #     user_prompt = "Продается 5-комн. квартира, 226,9 м² в ЖК «Дом на Мосфильмовской». Адрес Москва, Мосфильмовская ул., 88"

    #     # --- 1. Get real infrastructure data from 2GIS ---
    #     # print("\n--- Fetching Infrastructure Data from 2GIS ---")
    #     # two_gis_client = two_gis_client.TwoGisClient(api_key=TWOGIS_API_KEY)
    #     # infra_summary = two_gis_client.get_infrastructure_summary(real_address)
    #     # if not infra_summary:
    #     #     print("Could not get infrastructure data, continuing without it.")
    #     # else:
    #     #     print(infra_summary)
        
    #     # --- 2. Get real images ---
    #     image_dir = "/Users/grievous/Documents/agent/imgs"
    #     image_paths = []
    #     if os.path.exists(image_dir) and os.path.isdir(image_dir):
    #         print(f"\n--- Loading images from {image_dir} ---")
    #         for filename in os.listdir(image_dir):
    #             if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
    #                 image_paths.append(os.path.join(image_dir, filename))
            
    #         if image_paths:
    #             print(f"Found {len(image_paths)} images: {', '.join(os.path.basename(p) for p in image_paths)}")
    #         else:
    #             print("No images found in the directory.")
    #     else:
    #         print(f"Warning: Image directory not found at {image_dir}")

    #     # --- 3. Run the OpenAI client with real data ---
    #     ai_client = OpenAIClient(api_key=OPENAI_API_KEY)
    #     print("\n--- Generated Description ---")
    #     print(description) 