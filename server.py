from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Initialize the Flask app
app = Flask("modelserver")

# Load the model and tokenizer once, when the server starts
print("Loading the model...")
model_name = "../python_exp/models/deepseek-coder-1.3b-instruct"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
tokenizer = AutoTokenizer.from_pretrained(model_name)
print("Model loaded and ready to serve requests.")

@app.route("/generate", methods=["POST"])
def generate_text():
    try:
        # Get the input JSON payload
        data = request.json

        # Extract the input text and optional parameters
        input_text = data.get("text", "")
        # max_length = data.get("max_length", 50)
        # temperature = data.get("temperature", 0.7)
        # top_k = data.get("top_k", 50)

        # Ensure the input text is provided
        if not input_text:
            return jsonify({"error": "Input text is required"}), 400

        messages=[
            { 'role': 'user', 
              'content': input_text}]
        
        inputs = tokenizer.apply_chat_template(
                    messages, 
                    add_generation_prompt=True, 
                    return_tensors="pt"
                ).to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                                    inputs, 
                                    max_new_tokens=512, 
                                    do_sample=True, 
                                    top_k=50, 
                                    top_p=0.95, 
                                    num_return_sequences=1, 
                                    eos_token_id=tokenizer.eos_token_id
                                )
            
            generated_text = tokenizer.decode(
                                outputs[0][len(inputs[0]):], 
                                skip_special_tokens=True
                            )
            # Return the generated text as JSON
            return jsonify({"generated_text": generated_text}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def health_check():
    return jsonify({"message": "Model API is up and running!"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
