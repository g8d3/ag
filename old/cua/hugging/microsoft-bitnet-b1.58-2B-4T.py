from transformers import BitNetForCausalLM, AutoTokenizer

model_name = "microsoft/bitnet-b1.58-2B-4T"

try:
    model = BitNetForCausalLM.from_pretrained(model_name, trust_remote_code=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    inputs = tokenizer("Who are you?", return_tensors="pt")
    outputs = model.generate(**inputs)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(response)

except Exception as e:
    print(f"Error loading model: {e}")