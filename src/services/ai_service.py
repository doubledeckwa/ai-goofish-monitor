"""
AI Analysis Services
encapsulation AI Analyze relevant business logic
"""
from typing import Dict, List, Optional
from src.infrastructure.external.ai_client import AIClient


class AIAnalysisService:
    """AI Analysis Services"""

    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client

    async def analyze_product(
        self,
        product_data: Dict,
        image_paths: List[str],
        prompt_text: str
    ) -> Optional[Dict]:
        """
        Analyze products

        Args:
            product_data: Product data
            image_paths: Image path list
            prompt_text: Analyze prompt words

        Returns:
            Analyze results
        """
        if not self.ai_client.is_available():
            print("AI Client unavailable, skip analysis")
            return None

        try:
            result = await self.ai_client.analyze(product_data, image_paths, prompt_text)

            if result and self._validate_result(result):
                return result
            else:
                print("AI Analysis result verification failed")
                return None
        except Exception as e:
            print(f"AI Analysis service error: {e}")
            return None

    def _validate_result(self, result: Dict) -> bool:
        """verify AI Format of analysis results"""
        required_fields = [
            "prompt_version",
            "is_recommended",
            "reason",
            "risk_tags",
            "criteria_analysis"
        ]

        # Check required fields
        for field in required_fields:
            if field not in result:
                print(f"AI Response is missing a required field: {field}")
                return False

        # Check data type
        if not isinstance(result.get("is_recommended"), bool):
            print("is_recommended Field is not of type boolean")
            return False

        if not isinstance(result.get("risk_tags"), list):
            print("risk_tags Field is not a list type")
            return False

        criteria_analysis = result.get("criteria_analysis", {})
        if not isinstance(criteria_analysis, dict) or not criteria_analysis:
            print("criteria_analysis Must be a non-empty dictionary")
            return False

        return True
