class PromptManager:
    @staticmethod
    def get_prompt(agent_name: str) -> str:
        # In a real scenario, this would load from a file or database.
        # For simplicity, returning a basic template string based on agent name.
        return f"You are a PRism AI {agent_name} Agent. Review the provided code and identify issues based on your specialization."
