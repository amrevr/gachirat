from flask import Flask, render_template, send_from_directory, request, jsonify
import google.generativeai as genai
import os
import socket
from food_classifier import classify_food, get_nutrition_info
from database import get_db, init_db, test_connection, User, Conversation, FoodLog

app = Flask(__name__, 
            static_folder='../frontend',
            template_folder='../frontend')

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize database on startup
with app.app_context():
    if test_connection():
        init_db()
        print("[DEBUG] Flask app connected to PostgreSQL")

# Common prompt constraints
PROMPT_CONSTRAINTS = "Do NOT use any emoji. Use text emoticons like ^_^, :3, or :) in your own replies, but never use emoji. Do not describe actions in asterisks (e.g., *squeaks*). Avoid using asterisks for actions. Do not use the word 'fun' in your response."
PROMPT_CONSTRAINTS_NO_TUMMY = PROMPT_CONSTRAINTS + " Do not use the word 'tummy' or any of its synonyms (like stomach, belly, gut, abdomen, etc.) in your response."

# Helper function to generate LLM response
def generate_llm_response(prompt, word_limit=30):
    """Generate response from Gemini with consistent settings"""
    full_prompt = f"{prompt} Limit your response to {word_limit} words. {PROMPT_CONSTRAINTS}"
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(full_prompt)
    return response.text.strip() if hasattr(response, 'text') else str(response)

# Helper function to get or create user by username
def get_or_create_user(db, username='default_user'):
    """Get existing user or create new one. Uses provided db session."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username)
        db.add(user)
        db.flush()  # Flush to get the user ID without committing
        print(f"[DEBUG] Created new user: {username} (ID: {user.id})")
    else:
        print(f"[DEBUG] Found existing user: {username} (ID: {user.id})")
    
    # Special handling for "dead_user" - always reset health to 0
    if username == 'dead_user':
        user.health = 0
        print(f"[DEBUG] Reset dead_user health to 0")
    
    return user

# Helper function to retrieve relevant past conversations for RAG
def get_relevant_history(db, user_id, conversation_type='general', limit=10):
    """
    Retrieve past conversations filtered by type for RAG context.
    
    conversation_type:
    - 'food': food-related conversations (food_discussion, food_image_request)
    - 'general': general chat conversations (general_chat)
    - 'financial': financial advice conversations (financial_advice)
    """
    if conversation_type == 'food':
        states = ['food_discussion', 'food_image_request']
    elif conversation_type == 'financial':
        states = ['financial_advice']
    else:
        states = ['general_chat']
    
    conversations = db.query(Conversation).filter(
        Conversation.user_id == user_id,
        Conversation.conversation_state.in_(states)
    ).order_by(Conversation.timestamp.desc()).limit(limit).all()
    
    # Reverse to show oldest first (chronological order)
    conversations.reverse()
    
    # Format as context string
    if not conversations:
        return ""
    
    context_lines = []
    for conv in conversations:
        context_lines.append(f"User: {conv.user_message}")
        context_lines.append(f"Gachirat: {conv.bot_response}")
    
    return "\n".join(context_lines)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'success': False, 'message': 'Username is required'}), 400
    
    try:
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        
        if user:
            # Existing user - generate two greetings
            # Get recent food logs
            recent_foods = db.query(FoodLog).filter(
                FoodLog.user_id == user.id
            ).order_by(FoodLog.timestamp.desc()).limit(3).all()
            
            # Build context for greeting
            context = f"User {username} is returning. Health: {user.health}/20."
            if recent_foods:
                avg_health_score = sum(f.health_score for f in recent_foods) / len(recent_foods)
                context += f" Recent food health average: {avg_health_score:.1f}/5."
                food_list = ", ".join([f.food_name for f in recent_foods])
                context += f" Recent foods: {food_list}."
            
            # Simple login screen greeting
            login_greeting = f"Welcome back, {username}!"
            
            # Generate DETAILED chat window greeting
            chat_prompt = f"""You are Gachirat, a friendly digital pet rat. {context}

Generate a warm welcome message that:
1. Greets {username} by name
2. Briefly explains what you can help with (chat, food tracking, health advice)
3. Personalizes the end based on their recent behavior:
   - If health is high (11+) and recent foods were healthy (avg 4+): Praise and encourage them
   - If health is medium (7-10) or mixed foods: Gently motivate balance
   - If health is low (<7) or unhealthy foods: Motivate change with empathy

Keep it under 50 words, friendly, and use text emoticons like :3 or ^_^. Do NOT use emoji or asterisks for actions."""

            chat_greeting = generate_llm_response(chat_prompt, word_limit=50)
            
            print(f"[DEBUG] Login: {username} (existing user, ID: {user.id})")
            return jsonify({
                'success': True,
                'message': login_greeting,
                'chat_greeting': chat_greeting,
                'user_id': user.id,
                'health': user.health,
                'is_new': False
            })
        else:
            # New user - create account with two greetings
            new_user = User(username=username)
            db.add(new_user)
            db.commit()
            
            # Simple login screen greeting
            login_greeting = f"Account created. Welcome, {username}!"
            
            # Generate DETAILED chat window greeting
            chat_prompt = f"""You are Gachirat, a friendly digital pet rat. {username} is a new user.

Generate a warm welcome message that:
1. Introduces yourself as Gachirat
2. Explains you can chat, track food, and give health advice
3. Encourages them to share what they eat to help manage their health

Keep it under 50 words, friendly and enthusiastic. Use text emoticons like :3 or ^_^. Do NOT use emoji or asterisks for actions."""

            chat_greeting = generate_llm_response(chat_prompt, word_limit=50)
            
            print(f"[DEBUG] Login: {username} (new user created, ID: {new_user.id})")
            return jsonify({
                'success': True,
                'message': login_greeting,
                'chat_greeting': chat_greeting,
                'user_id': new_user.id,
                'health': new_user.health,
                'is_new': True
            })
    except Exception as e:
        print(f"✗ Login error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        db.close()

@app.route('/api/gemini', methods=['POST'])
def gemini_response():
    data = request.get_json()
    user_input = data.get('input', '')
    conversation_state = data.get('conversation_state', 'initial')
    username = data.get('username')
    
    if not username:
        return jsonify({'response': 'Username required'}), 400
    
    if not user_input:
        return jsonify({'response': 'No input provided.'}), 400
    
    # Single database session for entire request
    db = next(get_db())
    
    try:
        # Get or create user
        user = get_or_create_user(db, username)
        print(f"Processing request for user: {username} (ID: {user.id})")
        
        # Check if this is a food-related query
        food_keywords = ['hungry', 'eat', 'food', 'feed', 'meal', 'breakfast', 'lunch', 'dinner', 'snack', 'healthy', 'nutrition', 'calories', 'diet', 'ate']
        is_food_query = any(keyword in user_input.lower() for keyword in food_keywords)
        
        # Check if this is a financial advice query
        finance_keywords = ['money', 'finance', 'financial', 'invest', 'investment', 'stock', 'stocks', 'crypto', 'cryptocurrency', 'bitcoin', 'save', 'savings', 'budget', 'expense', 'debt', 'loan', 'credit', 'bank', 'portfolio', 'retirement', '401k', 'ira', 'dividend', 'etf', 'bond', 'mutual fund', 'tax', 'wealth', 'rich', 'poor', 'afford', 'cost', 'price', 'dollar', 'euro', 'yen']
        is_finance_query = any(keyword in user_input.lower() for keyword in finance_keywords)

        # Check if user is asking about what they last ate
        last_ate_keywords = [
            'what did i eat',
            'what was the last thing i ate',
            'what did i last eat',
            'last food',
            'last meal',
            'last thing i ate',
            'last thing eaten',
            'last thing you saw me eat',
            'last thing i showed you',
            'last food log',
            'last food entry',
            'last food classification',
            'what did i show you',
            'what did i upload',
            'what was my last upload',
            'what was my last food',
            'what was my last meal',
        ]
        is_last_ate_query = any(kw in user_input.lower() for kw in last_ate_keywords)

        if is_last_ate_query:
            # Retrieve the last food log for this user
            last_food = db.query(FoodLog).filter(FoodLog.user_id == user.id).order_by(FoodLog.timestamp.desc()).first()
            if last_food:
                last_food_str = f"The last thing you ate was {last_food.food_name} (category: {last_food.category}, health score: {last_food.health_score})."
            else:
                last_food_str = "I don't have any record of your last meal."
            prompt = f"You are Gachirat, a friendly digital pet rat. The user asked: '{user_input}'. {last_food_str} Answer the user's question using this information. Keep it brief and in character."
            text = generate_llm_response(prompt)
            # Log conversation
            conversation = Conversation(
                user_id=user.id,
                user_message=user_input,
                bot_response=text,
                conversation_state='food_log_lookup'
            )
            db.add(conversation)
            db.commit()
            print(f"[DEBUG] Saved conversation for {username} (food_log_lookup)")
            return jsonify({'response': text, 'is_food_query': False, 'conversation_state': 'initial'})
        
        # Check if user is describing food (after initial food query)
        show_upload = False
        
        # Reset conversation state keywords if user declines
        decline_keywords = ['no', 'nah', 'nope', 'not', "don't", "dont", 'never mind', 'nevermind', 'maybe later', 'later', "can't", 'cant']
        
        if is_food_query and conversation_state == 'initial':
            # Retrieve past food-related conversations for context
            history = get_relevant_history(db, user.id, conversation_type='food', limit=5)
            context_prompt = f"\n\nPrevious food conversations:\n{history}\n\n" if history else ""
            
            # First step: Ask user to describe the food
            prompt = f"You are Gachirat, a friendly digital pet rat who loves food.{context_prompt}The user said: '{user_input}'. Respond enthusiastically and ask them to describe what they ate or are eating. Avoid asking what the food is directly. Keep it brief and in character as a curious rat. Ask questions like how it tastes, etc. {PROMPT_CONSTRAINTS_NO_TUMMY}"
            text = generate_llm_response(prompt)
            
            # Log conversation to database
            conversation = Conversation(
                user_id=user.id,
                user_message=user_input,
                bot_response=text,
                conversation_state='food_discussion'
            )
            db.add(conversation)
            db.commit()
            print(f"[DEBUG] Saved conversation for {username}")
            
            return jsonify({'response': text, 'is_food_query': True, 'conversation_state': 'awaiting_description'})
        elif conversation_state == 'awaiting_description':
            # Check if user is declining to share
            is_decline = any(keyword in user_input.lower() for keyword in decline_keywords)
            
            if is_decline:
                # User declined, respond normally and reset state
                prompt = f"You are Gachirat, a friendly digital pet rat. The user said: '{user_input}'. They seem to not want to share right now. Respond kindly and understandingly, maybe a bit disappointed but still friendly. Keep it brief."
                text = generate_llm_response(prompt)
                
                # Log with general_chat state
                conversation = Conversation(
                    user_id=user.id,
                    user_message=user_input,
                    bot_response=text,
                    conversation_state='general_chat'
                )
                db.add(conversation)
                db.commit()
                print(f"[DEBUG] Saved conversation for {username}")
                
                return jsonify({'response': text, 'is_food_query': False, 'conversation_state': 'initial', 'hide_upload': True})
            else:
                # Retrieve past food conversations for context
                history = get_relevant_history(db, user.id, conversation_type='food', limit=5)
                context_prompt = f"\n\nPrevious food conversations:\n{history}\n\n" if history else ""
                
                # Second step: After description, ask to see the image
                prompt = f"You are Gachirat, a friendly digital pet rat.{context_prompt}The user described their food: '{user_input}'. Respond with excitement and curiosity, then say something like 'Let me see!' or 'Show me!' to prompt them to upload an image. Keep it brief and enthusiastic. {PROMPT_CONSTRAINTS_NO_TUMMY}"
                text = generate_llm_response(prompt)
                show_upload = True
                
                # Log with food_image_request state
                conversation = Conversation(
                    user_id=user.id,
                    user_message=user_input,
                    bot_response=text,
                    conversation_state='food_image_request'
                )
                db.add(conversation)
                db.commit()
                print(f"[DEBUG] Saved conversation for {username}")
                
            return jsonify({'response': text, 'is_food_query': True, 'show_upload': show_upload, 'conversation_state': 'awaiting_image'})
        elif conversation_state == 'awaiting_image':
            # Check if user is declining to upload image
            is_decline = any(keyword in user_input.lower() for keyword in decline_keywords)
            
            if is_decline:
                # User declined to upload, respond and reset
                prompt = f"You are Gachirat, a friendly digital pet rat. The user said: '{user_input}' when you asked to see their food. Respond understandingly but a bit sad. Keep it brief and friendly."
                text = generate_llm_response(prompt)
                
                # Log with general_chat state
                conversation = Conversation(
                    user_id=user.id,
                    user_message=user_input,
                    bot_response=text,
                    conversation_state='general_chat'
                )
                db.add(conversation)
                db.commit()
                print(f"[DEBUG] Saved conversation for {username}")
                
                return jsonify({'response': text, 'is_food_query': False, 'conversation_state': 'initial', 'hide_upload': True})
            else:
                # User said something else, remind them gently to upload
                prompt = f"You are Gachirat, a friendly digital pet rat. You asked to see the user's food and they responded: '{user_input}'. Gently remind them to upload an image if they have one, or acknowledge what they said. Keep it brief and friendly."
                text = generate_llm_response(prompt)
                
                # Log with food_image_request state
                conversation = Conversation(
                    user_id=user.id,
                    user_message=user_input,
                    bot_response=text,
                    conversation_state='food_image_request'
                )
                db.add(conversation)
                db.commit()
                print(f"[DEBUG] Saved conversation for {username}")
                
                return jsonify({'response': text, 'is_food_query': True, 'show_upload': True, 'conversation_state': 'awaiting_image'})
        elif is_finance_query:
            # Retrieve past financial advice conversations for context
            history = get_relevant_history(db, user.id, conversation_type='financial', limit=5)
            context_prompt = f"\n\nPrevious financial conversations:\n{history}\n\n" if history else ""
            
            # Financial advice feature with RAG context
            prompt = f"You are Gachirat, a street-smart digital pet rat with surprising financial wisdom from living in the urban jungle.{context_prompt}The user asked: '{user_input}'. Give them practical, savvy financial advice in character - be enthusiastic and confident like a rat who knows how to find the best deals and stash resources wisely. Keep it brief and actionable."
            text = generate_llm_response(prompt, word_limit=50)
            
            # Log conversation to database
            conversation = Conversation(
                user_id=user.id,
                user_message=user_input,
                bot_response=text,
                conversation_state='financial_advice'
            )
            db.add(conversation)
            db.commit()
            print(f"[DEBUG] Saved financial advice conversation for {username}")
            
            return jsonify({'response': text, 'is_food_query': False, 'conversation_state': 'initial'})
        else:
            # Retrieve past general conversations for context
            history = get_relevant_history(db, user.id, conversation_type='general', limit=5)
            context_prompt = f"\n\nPrevious conversations:\n{history}\n\n" if history else ""
            
            # Normal conversation
            prompt = f"You are Gachirat, a friendly digital pet rat.{context_prompt}The user said: '{user_input}'. Respond in character."
            text = generate_llm_response(prompt)
            
            # Log conversation to database
            conversation = Conversation(
                user_id=user.id,
                user_message=user_input,
                bot_response=text,
                conversation_state='general_chat'
            )
            db.add(conversation)
            db.commit()
            print(f"[DEBUG] Saved conversation for {username}")
            
            return jsonify({'response': text, 'is_food_query': False, 'conversation_state': 'initial'})
    except Exception as e:
        print(f"✗ Gemini error: {str(e)}")
        return jsonify({'response': f'Error: {str(e)}'}), 500
    finally:
        db.close()

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
            prompt = f"You are Gachirat, a friendly digital pet rat. The user showed you a picture of {food_name} (a {category}). This is very healthy food! Respond excitedly and praise them for eating healthy. Keep it brief and encouraging. Mention the specific food. {PROMPT_CONSTRAINTS_NO_TUMMY}"
        elif health_score == 3:
            prompt = f"You are Gachirat, a friendly digital pet rat. The user showed you a picture of {food_name} (a {category}). This is moderately healthy. Respond positively but suggest balance. Keep it brief and friendly. Mention the specific food. {PROMPT_CONSTRAINTS_NO_TUMMY}"
        else:
            prompt = f"You are Gachirat, a friendly digital pet rat. The user showed you a picture of {food_name} (a {category}). This is not very healthy. Respond playfully but gently suggest healthier options next time. Keep it brief, non-judgmental, and friendly. Mention the specific food. {PROMPT_CONSTRAINTS_NO_TUMMY}"
        
        text = generate_llm_response(prompt)
        
        # Log food entry to database
        username = request.form.get('username')
        if not username:
            return jsonify({'response': 'Username required'}), 400
        
        db = next(get_db())
        user = get_or_create_user(db, username)
        
        # Calculate health change based on food category
        # Fruits/Vegetables (health_score 4-5): add health_score
        # Neutral foods (health_score 3): no change
        # Unhealthy foods (health_score 1-2): subtract (6 - health_score) to penalize more
        if category in ['fruit', 'vegetable'] and health_score >= 4:
            health_change = health_score
        elif health_score >= 3:
            health_change = 0
        else:
            health_change = -(6 - health_score)  # -5 for score 1, -4 for score 2
        
        # Update user health (0-20 range)
        old_health = user.health
        user.health = max(0, min(20, user.health + health_change))
        new_health = user.health
        
        print(f"Health update for {username}: {old_health} -> {new_health} (change: {health_change})")
        
        food_log = FoodLog(
            user_id=user.id,
            food_name=food_name,
            category=category,
            health_score=health_score,
            confidence=confidence
        )
        db.add(food_log)
        db.commit()
        db.close()
        
        # Check if food is healthy (fruits/vegetables with score 4-5)
        is_healthy_food = category in ['fruit', 'vegetable'] and health_score >= 4
        
        return jsonify({
            'response': text,
            'food_name': food_name,
            'health_score': health_score,
            'category': category,
            'confidence': confidence,
            'health': new_health,
            'health_change': health_change,
            'is_healthy_food': is_healthy_food,
            'hide_upload': True
        })
    except Exception as e:
        return jsonify({'response': f'Error: {str(e)}'}), 500

@app.route('/api/esp32', methods=['POST'])
def send_to_esp32():
    """Send emotion code to ESP32 via UDP"""
    try:
        data = request.get_json()
        emotion = data.get('emotion')
        ip = data.get('ip', '192.168.0.21')
        port = data.get('port', 5005)
        
        if emotion is None:
            return jsonify({'success': False, 'message': 'No emotion provided'}), 400
        
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)  # 1 second timeout
        
        # Send emotion as single byte
        message = bytes([emotion])
        sock.sendto(message, (ip, port))
        sock.close()
        
        print(f"[DEBUG] Sent emotion {emotion} to ESP32 at {ip}:{port}")
        return jsonify({'success': True, 'emotion': emotion})
        
    except socket.timeout:
        print(f"[ERROR] ESP32 socket timeout")
        return jsonify({'success': False, 'message': 'ESP32 timeout'}), 500
    except Exception as e:
        print(f"[ERROR] ESP32 communication error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
