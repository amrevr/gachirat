from flask import Flask, render_template, send_from_directory, request, jsonify
import google.generativeai as genai
import os
from food_classifier import classify_food, get_nutrition_info

app = Flask(__name__, 
            static_folder='../frontend',
            template_folder='../frontend')

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@app.route('/api/gemini', methods=['POST'])
def gemini_response():
    data = request.get_json()
    user_input = data.get('input', '')
    conversation_state = data.get('conversation_state', 'initial')  # Track conversation flow
    
    if not user_input:
        return jsonify({'response': 'No input provided.'}), 400
    
    # Check if this is a food-related query
    food_keywords = ['hungry', 'eat', 'food', 'feed', 'meal', 'breakfast', 'lunch', 'dinner', 'snack', 'healthy', 'nutrition', 'calories', 'diet', 'ate']
    is_food_query = any(keyword in user_input.lower() for keyword in food_keywords)
    
    # Check if user is describing food (after initial food query)
    show_upload = False
    
    # Reset conversation state keywords if user declines
    decline_keywords = ['no', 'nah', 'nope', 'not', "don't", "dont", 'never mind', 'nevermind', 'maybe later', 'later', "can't", 'cant']

    try:
        if is_food_query and conversation_state == 'initial':
            # First step: Ask user to describe the food
            prompt = f"You are Gachirat, a friendly digital pet rat who loves food. The user said: '{user_input}'. Respond enthusiastically and ask them to describe what they ate or are eating. Keep it brief and in character as a curious rat. Ask questions like what it is, how it tastes, etc. Do NOT use any emoji. Limit your response to 30 words. Use text emoticons like ^_^, :3, or :) in your own replies, but never use emoji. Do not describe actions in asterisks (e.g., *squeaks*). Avoid using asterisks for actions. Do not use the word 'fun' in your response. Do not use the word 'tummy' or any of its synonyms (like stomach, belly, gut, abdomen, etc.) in your response."
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            text = response.text.strip() if hasattr(response, 'text') else str(response)
            return jsonify({'response': text, 'is_food_query': True, 'conversation_state': 'awaiting_description'})
        elif conversation_state == 'awaiting_description':
            # Check if user is declining to share
            is_decline = any(keyword in user_input.lower() for keyword in decline_keywords)
            
            if is_decline:
                # User declined, respond normally and reset state
                prompt = f"You are Gachirat, a friendly digital pet rat. The user said: '{user_input}'. They seem to not want to share right now. Respond kindly and understandingly, maybe a bit disappointed but still friendly. Keep it brief. Do NOT use any emoji. Limit your response to 30 words. Use text emoticons like ^_^, :3, or :) in your own replies, but never use emoji. Do not describe actions in asterisks (e.g., *squeaks*). Avoid using asterisks for actions. Do not use the word 'fun' in your response."
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                text = response.text.strip() if hasattr(response, 'text') else str(response)
                return jsonify({'response': text, 'is_food_query': False, 'conversation_state': 'initial', 'hide_upload': True})
            else:
                # Second step: After description, ask to see the image
                prompt = f"You are Gachirat, a friendly digital pet rat. The user described their food: '{user_input}'. Respond with excitement and curiosity, then say something like 'Let me see!' or 'Show me!' to prompt them to upload an image. Keep it brief and enthusiastic. Do NOT use any emoji. Limit your response to 30 words. Use text emoticons like ^_^, :3, or :) in your own replies, but never use emoji. Do not describe actions in asterisks (e.g., *squeaks*). Avoid using asterisks for actions. Do not use the word 'fun' in your response. Do not use the word 'tummy' or any of its synonyms (like stomach, belly, gut, abdomen, etc.) in your response."
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                text = response.text.strip() if hasattr(response, 'text') else str(response)
                show_upload = True
            return jsonify({'response': text, 'is_food_query': True, 'show_upload': show_upload, 'conversation_state': 'awaiting_image'})
        elif conversation_state == 'awaiting_image':
            # Check if user is declining to upload image
            is_decline = any(keyword in user_input.lower() for keyword in decline_keywords)
            
            if is_decline:
                # User declined to upload, respond and reset
                prompt = f"You are Gachirat, a friendly digital pet rat. The user said: '{user_input}' when you asked to see their food. Respond understandingly but a bit sad. Keep it brief and friendly. Do NOT use any emoji. Limit your response to 30 words. Use text emoticons like ^_^, :3, or :) in your own replies, but never use emoji. Do not describe actions in asterisks (e.g., *squeaks*). Avoid using asterisks for actions. Do not use the word 'fun' in your response."
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                text = response.text.strip() if hasattr(response, 'text') else str(response)
                return jsonify({'response': text, 'is_food_query': False, 'conversation_state': 'initial', 'hide_upload': True})
            else:
                # User said something else, remind them gently to upload
                prompt = f"You are Gachirat, a friendly digital pet rat. You asked to see the user's food and they responded: '{user_input}'. Gently remind them to upload an image if they have one, or acknowledge what they said. Keep it brief and friendly. Do NOT use any emoji. Limit your response to 30 words. Use text emoticons like ^_^, :3, or :) in your own replies, but never use emoji. Do not describe actions in asterisks (e.g., *squeaks*). Avoid using asterisks for actions. Do not use the word 'fun' in your response."
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                text = response.text.strip() if hasattr(response, 'text') else str(response)
                return jsonify({'response': text, 'is_food_query': True, 'show_upload': True, 'conversation_state': 'awaiting_image'})
        else:
            # Normal conversation
            prompt = f"You are Gachirat, a friendly digital pet rat. The user said: '{user_input}'. Respond in character. Do NOT use any emoji. Limit your response to 30 words. Use text emoticons like ^_^, :3, or :) in your own replies, but never use emoji. Do not describe actions in asterisks (e.g., *squeaks*). Avoid using asterisks for actions. Do not use the word 'fun' in your response."
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            text = response.text.strip() if hasattr(response, 'text') else str(response)
            return jsonify({'response': text, 'is_food_query': False, 'conversation_state': 'initial'})
    except Exception as e:
        return jsonify({'response': f'Error: {str(e)}'}), 500

@app.route('/api/feed', methods=['POST'])
def feed_animal():
    if 'image' not in request.files:
        return jsonify({'response': 'No image provided.'}), 400
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'response': 'No image selected.'}), 400
    
    try:
        # Reset file pointer to beginning before classification
        image_file.seek(0)
        
        # Classify the food
        food_name, confidence = classify_food(image_file)
        
        # Get nutrition info
        nutrition = get_nutrition_info(food_name)
        
        # Generate response based on health score
        health_score = nutrition['health_score']
        category = nutrition['category']
        
        # Create personalized response using Gemini
        if health_score >= 4:
            prompt = f"You are Gachirat, a friendly digital pet rat. The user showed you a picture of {food_name} (a {category}). This is very healthy food! Respond excitedly and praise them for eating healthy. Keep it brief and encouraging. Mention the specific food. Do NOT use any emoji. Limit your response to 30 words. Use text emoticons like ^_^, :3, or :) in your own replies, but never use emoji. Do not describe actions in asterisks (e.g., *squeaks*). Avoid using asterisks for actions. Do not use the word 'fun' in your response. Do not use the word 'tummy' or any of its synonyms (like stomach, belly, gut, abdomen, etc.) in your response."
        elif health_score == 3:
            prompt = f"You are Gachirat, a friendly digital pet rat. The user showed you a picture of {food_name} (a {category}). This is moderately healthy. Respond positively but suggest balance. Keep it brief and friendly. Mention the specific food. Do NOT use any emoji. Limit your response to 30 words. Use text emoticons like ^_^, :3, or :) in your own replies, but never use emoji. Do not describe actions in asterisks (e.g., *squeaks*). Avoid using asterisks for actions. Do not use the word 'fun' in your response. Do not use the word 'tummy' or any of its synonyms (like stomach, belly, gut, abdomen, etc.) in your response."
        else:
            prompt = f"You are Gachirat, a friendly digital pet rat. The user showed you a picture of {food_name} (a {category}). This is not very healthy. Respond playfully but gently suggest healthier options next time. Keep it brief, non-judgmental, and friendly. Mention the specific food. Do NOT use any emoji. Limit your response to 30 words. Use text emoticons like ^_^, :3, or :) in your own replies, but never use emoji. Do not describe actions in asterisks (e.g., *squeaks*). Avoid using asterisks for actions. Do not use the word 'fun' in your response. Do not use the word 'tummy' or any of its synonyms (like stomach, belly, gut, abdomen, etc.) in your response."
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        text = response.text.strip() if hasattr(response, 'text') else str(response)
        
        return jsonify({
            'response': text,
            'food_name': food_name,
            'health_score': health_score,
            'category': category,
            'confidence': confidence
        })
    except Exception as e:
        return jsonify({'response': f'Error: {str(e)}'}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
