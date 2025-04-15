from transformers import pipeline, AutoConfig

try:
    config = AutoConfig.from_pretrained("microsoft/bitnet-b1.58-2B-4T", trust_remote_code=True)
    pipe = pipeline("text-generation", model="microsoft/bitnet-b1.58-2B-4T", config=config, trust_remote_code=True)
    messages = [
        {"role": "user", "content": "Who are you?"},
    ]
    response = pipe(messages)
    print(response)
except OSError as e:
    print(f"Error loading model: {e}")