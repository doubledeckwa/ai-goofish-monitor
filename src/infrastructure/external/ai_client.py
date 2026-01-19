"""
AI client encapsulation
Provide a unified AI Call interface
"""
import os
import json
import base64
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI
from src.infrastructure.config.settings import AISettings
from src.infrastructure.config.env_manager import env_manager


class AIClient:
    """AI client encapsulation"""

    def __init__(self):
        self.settings: Optional[AISettings] = None
        self.client: Optional[AsyncOpenAI] = None
        self.refresh()

    def _load_settings(self) -> None:
        load_dotenv(dotenv_path=env_manager.env_file, override=True)
        self.settings = AISettings()

    def refresh(self) -> None:
        self._load_settings()
        self.client = self._initialize_client()

    def _initialize_client(self) -> Optional[AsyncOpenAI]:
        """initialization OpenAI client"""
        if not self.settings or not self.settings.is_configured():
            print("warn：AI Incomplete configuration，AI Features will be unavailable")
            return None

        try:
            if self.settings.proxy_url:
                print(f"working on AI Request to use proxy: {self.settings.proxy_url}")
                os.environ['HTTP_PROXY'] = self.settings.proxy_url
                os.environ['HTTPS_PROXY'] = self.settings.proxy_url

            return AsyncOpenAI(
                api_key=self.settings.api_key,
                base_url=self.settings.base_url
            )
        except Exception as e:
            print(f"initialization AI Client failed: {e}")
            return None

    def is_available(self) -> bool:
        """examine AI Is the client available?"""
        return self.client is not None

    @staticmethod
    def encode_image(image_path: str) -> Optional[str]:
        """Encode the image as Base64"""
        if not image_path or not os.path.exists(image_path):
            return None
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"Failed to encode image: {e}")
            return None

    async def analyze(
        self,
        product_data: Dict,
        image_paths: List[str],
        prompt_text: str
    ) -> Optional[Dict]:
        """
        Analyze product data

        Args:
            product_data: Product data
            image_paths: Image path list
            prompt_text: Analyze prompt words

        Returns:
            Analyze results
        """
        if not self.is_available():
            print("AI Client is unavailable")
            return None

        try:
            messages = self._build_messages(product_data, image_paths, prompt_text)
            response = await self._call_ai(messages)
            return self._parse_response(response)
        except Exception as e:
            print(f"AI Analysis failed: {e}")
            return None

    def _build_messages(self, product_data: Dict, image_paths: List[str], prompt_text: str) -> List[Dict]:
        """build AI information"""
        product_json = json.dumps(product_data, ensure_ascii=False, indent=2)
        text_prompt = f"""Please analyze the complete offer below based on your expertise and my requirementsJSONdata：

```json
{product_json}
```

{prompt_text}
"""
        user_content = []

        # Add pictures first
        for path in image_paths:
            base64_img = self.encode_image(path)
            if base64_img:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
                })

        # Add more text
        user_content.append({"type": "text", "text": text_prompt})

        return [{"role": "user", "content": user_content}]

    async def _call_ai(self, messages: List[Dict]) -> str:
        """call AI API"""
        request_params = {
            "model": self.settings.model_name,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 4000
        }

        # Add optional parameters based on configuration
        if self.settings.enable_response_format:
            request_params["response_format"] = {"type": "json_object"}

        if self.settings.enable_thinking:
            request_params["extra_body"] = {"enable_thinking": False}

        response = await self.client.chat.completions.create(**request_params)

        # Compatible with different API response format
        if hasattr(response, 'choices'):
            return response.choices[0].message.content
        return response

    def _parse_response(self, response_text: str) -> Optional[Dict]:
        """parse AI response"""
        try:
            # Direct analysis JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # clean up Markdown code block tag
            cleaned = response_text.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            # extract JSON object
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_str = cleaned[start:end + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass

            print(f"Unable to parse AI response: {response_text[:100]}")
            return None
