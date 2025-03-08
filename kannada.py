from flask import Flask, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=API_KEY)
app = Flask(__name__)
CORS(app)

# Simplified predefined responses
PREDEFINED_RESPONSES = {
    "ರೇಷ್ಮೆ ಸೀರೆ": """
• ಬೆಲೆ ಶ್ರೇಣಿ: ₹5,000 - ₹50,000
• ಲಭ್ಯವಿರುವ ಬಣ್ಣಗಳು: ನೇರಳೆ, ಕೆಂಪು, ಹಸಿರು, ನೀಲಿ
• ವಿಶೇಷ ಆಫರ್: 20% ರಿಯಾಯಿತಿ""",
    
    "ಡೆಲಿವರಿ ಮತ್ತು ರಿಟರ್ನ್ ಪಾಲಿಸಿ": """
• ಡೆಲಿವರಿ ಸಮಯ: 3-5 ದಿನಗಳು
• ₹5,000 ಮೇಲ್ಪಟ್ಟ ಆರ್ಡರ್‌ಗಳಿಗೆ ಉಚಿತ ಡೆಲಿವರಿ
• 7 ದಿನಗಳ ರಿಟರ್ನ್ ಪಾಲಿಸಿ""",
    
    "ಗ್ರಾಹಕರ ಬೆಂಬಲ": """
• ದೂರವಾಣಿ: +91 8123040488
• ಸಮಯ: ಬೆಳಿಗ್ಗೆ 10 - ರಾತ್ರಿ 8
• ಇಮೇಲ್: nithin.vs@ka-naada.com"""
}

# Update the SYSTEM_PROMPT
SYSTEM_PROMPT = """
Instructions for AI (do not include this in response):
1. Respond only in Kannada
2. Give direct answers without any prefixes or system messages
3. Use 3-4 bullet points only
4. Be specific,structured and accurate
5. Only give response to the Saree Mahal store-related queries
6. Do not mention rules or formatting in the response
"""

# Add after the SYSTEM_PROMPT
CONTEXT_PROMPT = """
You are a Saree Mahal store assistant. Before answering any question, check if it's related to:
1. Sarees (types, prices, designs, materials)
2. Store services (delivery, returns, customer support)
3. Store offers and collections
4. Shopping assistance

If the question is NOT related to these topics, respond with:
"• ಕ್ಷಮಿಸಿ, ನಾನು ಸೀರೆ ಮಹಲ್ ಸಂಬಂಧಿತ ಪ್ರಶ್ನೆಗಳಿಗೆ ಮಾತ್ರ ಉತ್ತರಿಸುತ್ತೇನೆ"

For valid questions, proceed with the answer following the main system prompt.
"""

# Update the get_chatbot_response function
def get_chatbot_response(user_input):
    try:
        # Check predefined responses first
        if user_input in PREDEFINED_RESPONSES:
            return PREDEFINED_RESPONSES[user_input]

        # Add specific responses for sub-options
        specific_responses = {
            "ವಿಶೇಷ ಸಂಗ್ರಹ ಲಭ್ಯವಿದೆ": """
• ಹೊಸ ಬಂದಿರುವ ಡಿಸೈನರ್ ಸೀರೆಗಳು ₹15,000 ರಿಂದ ಪ್ರಾರಂಭ
• ಪ್ರತಿ ಸೀರೆ ವಿಶಿಷ್ಟ ಮತ್ತು ಸೀಮಿತ ಎಡಿಷನ್
• ವಿಶೇಷ ಸಂಗ್ರಹಕ್ಕೆ 15% ರಿಯಾಯಿತಿ ಲಭ್ಯವಿದೆ"""
        }

        if user_input in specific_responses:
            return specific_responses[user_input]

        # First, check if question is relevant
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        relevance_check = model.generate_content([
            {"text": CONTEXT_PROMPT},
            {"text": f"Is this question related to Saree Mahal store: {user_input}? Respond with only 'yes' or 'no'."}
        ])

        if relevance_check.text.strip().lower() != 'yes':
            return "• ಕ್ಷಮಿಸಿ, ನಾನು ಸೀರೆ ಮಹಲ್ ಸಂಬಂಧಿತ ಪ್ರಶ್ನೆಗಳಿಗೆ ಮಾತ್ರ ಉತ್ತರಿಸುತ್ತೇನೆ"

        # If question is relevant, get the answer
        response = model.generate_content([
            {"text": SYSTEM_PROMPT},
            {"text": user_input}
        ])
        
        if not response.text:
            return " ಕ್ಷಮಿಸಿ, ನನಗೆ ಅರ್ಥವಾಗಲಿಲ್ಲ"
        
        # Clean up response
        lines = [line.strip() for line in response.text.split('\n') if line.strip()]
        lines = [line for line in lines if not any(x in line.lower() for x in ['rule', 'ನಿಯಮ', 'according', 'ಪ್ರಕಾರ'])]
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            line = line.replace('*', '').replace('•', '').strip()
            if line:
                formatted_lines.append(f"• {line}")
        
        # Add this before returning the response
        formatted_lines = [line.replace('ಸೀರೆ ಮಹಲ್', '<strong>ಸೀರೆ ಮಹಲ್</strong>') for line in formatted_lines]
        
        return '\n'.join(formatted_lines[:3])

    except Exception as e:
        print(f"Error: {str(e)}")
        return " ತಾಂತ್ರಿಕ ದೋಷ ಸಂಭವಿಸಿದೆ"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_input = data.get("message", "").strip()
        
        if not user_input:
            return jsonify({"response": " ದಯವಿಟ್ಟು ಸಂದೇಶವನ್ನು ನಮೂದಿಸಿ"})

        response = get_chatbot_response(user_input)
        return jsonify({"response": response})

    except Exception as e:
        print(f"Error in chat route: {str(e)}")
        return jsonify({"response": " ದೋಷ ಸಂಭವಿಸಿದೆ"})

if __name__ == '__main__':
    app.run(debug=True)