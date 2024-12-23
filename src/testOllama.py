"""Example usage of aisuite."""
import aisuite as ai
def main():
    # Initialize aisuite
    #ai = aisuite.AISuiteClient()
    client = ai.Client()
    messages = [
    {"role": "system", "content": "Respond in English."},
    {"role": "user", "content": "Tell me a joke about Captain Jack Sparrow"},
    ]
    # Set the model to use
    ai.set_model("llama:3.2")

    # Generate a response using the model
    prompt = "What is the capital of France?"
    response = ai.generate(prompt)

    # Print the response
    print(f"Prompt: {prompt}")
    print(f"Response: {response}")

if __name__ == "__main__":
    main()