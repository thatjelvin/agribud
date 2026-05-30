class CopilotProvider:
    def answer(self, question: str, context: dict) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class RuleBasedCopilotProvider(CopilotProvider):
    def answer(self, question: str, context: dict) -> str:
        if 'drought' in question.lower():
            return 'Current risk signals indicate water stress trends. Prioritize irrigation scheduling and moisture monitoring this week.'
        if 'yield' in question.lower():
            prediction = context.get('latest_prediction')
            if prediction:
                return f"Latest yield forecast is {prediction.predicted_yield_ton_ha:.2f} ton/ha with confidence {prediction.confidence_score:.0%}."
            return 'Yield prediction is not available yet. Trigger prediction from the analytics panel.'
        return 'I can explain farm health, weather, yield, and risk insights from your dashboard data.'
