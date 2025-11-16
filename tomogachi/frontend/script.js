let conversationState = 'initial';  // Track conversation state
let currentUsername = null;  // Track logged in user
let currentUserId = null;  // Track logged in user ID
let currentHealth = 20;  // Track current health
let currentMood = 'happy';  // Track current mood (happy, sad)

// ESP32 configuration
const ESP32_IP = '10.87.41.107';
const ESP32_PORT = 5005;

// ESP32 emotion enum mapping
const ESP32_EMOTIONS = {
  SAD: 0,
  SAD_NEUTRAL_TRANSITION: 1,
  NEUTRAL: 2,
  HAPPY_NEUTRAL_TRANSITION: 3,
  HAPPY: 4
};

// State table for GIF transitions and animations
const STATE_TABLE = {
  idle: {
    gif: 'tomo/3-idle.gif',
    esp32Emotion: ESP32_EMOTIONS.NEUTRAL,
    transitions: {
      happy: { 
        transition: 'tomo/31-idle-to-happy.gif', 
        duration: 1500,
        esp32Emotion: ESP32_EMOTIONS.HAPPY_NEUTRAL_TRANSITION
      },
      sad: { 
        transition: 'tomo/32-idle-to-sad.gif', 
        duration: 1500,
        esp32Emotion: ESP32_EMOTIONS.SAD_NEUTRAL_TRANSITION
      }
    }
  },
  happy: {
    gif: 'tomo/1-happy.gif',
    esp32Emotion: ESP32_EMOTIONS.HAPPY,
    transitions: {
      idle: { 
        transition: 'tomo/31-idle-to-happy.gif', 
        duration: 1500,
        esp32Emotion: ESP32_EMOTIONS.HAPPY_NEUTRAL_TRANSITION
      },
      sad: { 
        transition: 'tomo/32-idle-to-sad.gif', 
        duration: 1500,
        esp32Emotion: ESP32_EMOTIONS.SAD_NEUTRAL_TRANSITION
      }
    }
  },
  sad: {
    gif: 'tomo/2-sad.gif',
    esp32Emotion: ESP32_EMOTIONS.SAD,
    transitions: {
      idle: { 
        transition: 'tomo/32-idle-to-sad.gif', 
        duration: 1500,
        esp32Emotion: ESP32_EMOTIONS.SAD_NEUTRAL_TRANSITION
      },
      happy: { 
        transition: 'tomo/31-idle-to-happy.gif', 
        duration: 1500,
        esp32Emotion: ESP32_EMOTIONS.HAPPY_NEUTRAL_TRANSITION
      }
    }
  }
};

// Send emotion signal to ESP32
async function sendToESP32(emotionCode) {
  try {
    const response = await fetch('/api/esp32', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        emotion: emotionCode,
        ip: ESP32_IP,
        port: ESP32_PORT
      })
    });
    
    if (!response.ok) {
      console.warn('Failed to send emotion to ESP32:', response.statusText);
    }
  } catch (err) {
    console.warn('Error sending to ESP32:', err);
  }
}

// Periodic ESP32 heartbeat - send current state every 5 seconds
let esp32HeartbeatInterval = null;

function startESP32Heartbeat() {
  // Clear any existing interval
  if (esp32HeartbeatInterval) {
    clearInterval(esp32HeartbeatInterval);
  }
  
  // Send current state every 5 seconds
  esp32HeartbeatInterval = setInterval(() => {
    const currentEmotion = STATE_TABLE[currentMood]?.esp32Emotion;
    if (currentEmotion !== undefined) {
      sendToESP32(currentEmotion);
      console.log(`[ESP32 Heartbeat] Sent ${currentMood} (${currentEmotion})`);
    }
  }, 5000);
}

function stopESP32Heartbeat() {
  if (esp32HeartbeatInterval) {
    clearInterval(esp32HeartbeatInterval);
    esp32HeartbeatInterval = null;
  }
}

// Function to transition between states
function transitionToState(targetState) {
  const leftGif = document.getElementById('leftSectionGif');
  
  // If already in target state, do nothing
  if (currentMood === targetState) {
    return;
  }
  
  // Get transition info
  const currentStateInfo = STATE_TABLE[currentMood];
  const transition = currentStateInfo.transitions[targetState];
  
  if (transition) {
    // Send transition emotion to ESP32
    sendToESP32(transition.esp32Emotion);
    
    // Play transition animation
    leftGif.src = transition.transition;
    
    // After transition completes, switch to target state
    setTimeout(() => {
      leftGif.src = STATE_TABLE[targetState].gif;
      currentMood = targetState;
      
      // Send final state emotion to ESP32
      sendToESP32(STATE_TABLE[targetState].esp32Emotion);
    }, transition.duration);
  } else {
    // Direct transition if no animation defined
    leftGif.src = STATE_TABLE[targetState].gif;
    currentMood = targetState;
    
    // Send final state emotion to ESP32
    sendToESP32(STATE_TABLE[targetState].esp32Emotion);
  }
}

// Update health bar display
function updateHealthBar(health) {
  currentHealth = health;
  const healthFill = document.getElementById('healthBarFill');
  const healthText = document.getElementById('healthBarText');
  // Calculate percent fill for bar (out of 20)
  const percent = Math.max(0, Math.min(100, (health / 20) * 100));
  healthFill.style.width = percent + '%';
  healthText.textContent = health + '/20';
  
  // Update GIF based on health
  updateGifBasedOnHealth(health);
}

// Update GIF based on health status
function updateGifBasedOnHealth(health) {
  const targetMood = health <= 10 ? 'sad' : 'happy';
  transitionToState(targetMood);
}

// Reusable dot animation function
function animateDots(element, callback) {
  let dots = 0;
  let animating = true;
  let animationCycleDone = false;
  let responseData = null;
  
  element.textContent = '> .';
  
  const dotInterval = setInterval(() => {
    if (!animating) return;
    dots = (dots + 1) % 4;
    element.textContent = '> ' + '.'.repeat(dots || 1);
    if (dots === 3 && !animationCycleDone) {
      animationCycleDone = true;
      checkAndStop();
    }
  }, 400);
  
  function checkAndStop() {
    if (animationCycleDone && responseData !== null) {
      animating = false;
      clearInterval(dotInterval);
      callback(responseData);
    }
  }
  
  return {
    stop: function(data) {
      responseData = data;
      checkAndStop();
    }
  };
}

document.getElementById('playButton').addEventListener('click', function() {
  const initialView = document.getElementById('initialView');
  const loginView = document.getElementById('loginView');
  
  // Show login screen
  initialView.classList.add('hidden');
  loginView.classList.add('visible');
});

// Handle login
document.getElementById('loginButton').addEventListener('click', async function() {
  const username = document.getElementById('usernameInput').value.trim();
  const loginMessage = document.getElementById('loginMessage');
  const loginButton = document.getElementById('loginButton');
  
  if (!username) {
    loginMessage.textContent = 'Please enter a username';
    return;
  }
  
  // Disable button and start loading animation
  loginButton.disabled = true;
  loginButton.style.opacity = '0.6';
  loginButton.style.cursor = 'not-allowed';
  
  let dots = 0;
  loginButton.textContent = 'Loading.';
  const loadingInterval = setInterval(() => {
    dots = (dots + 1) % 4;
    loginButton.textContent = 'Loading' + '.'.repeat(dots || 1);
  }, 400);
  
  try {
    // Attempt to login/register
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username })
    });
    
    const data = await res.json();
    
    // Stop loading animation
    clearInterval(loadingInterval);
    
    if (data.success) {
      currentUsername = username;
      currentUserId = data.user_id;
      currentHealth = data.health || 100;
      loginMessage.textContent = data.message;  // Short login screen greeting
      
      // Start the game after brief delay and show detailed chat greeting
      setTimeout(() => {
        startGame(data.chat_greeting);  // Detailed chat window greeting
      }, 1000);
    } else {
      loginMessage.textContent = data.message || 'Login failed';
      // Re-enable button
      loginButton.disabled = false;
      loginButton.style.opacity = '1';
      loginButton.style.cursor = 'pointer';
      loginButton.textContent = 'Login';
    }
  } catch (err) {
    clearInterval(loadingInterval);
    loginMessage.textContent = 'Connection error';
    // Re-enable button
    loginButton.disabled = false;
    loginButton.style.opacity = '1';
    loginButton.style.cursor = 'pointer';
    loginButton.textContent = 'Login';
  }
});

// Allow Enter key for login
document.getElementById('usernameInput').addEventListener('keypress', function(e) {
  if (e.key === 'Enter') {
    document.getElementById('loginButton').click();
  }
});

function startGame(greetingMessage) {
  const container = document.getElementById('tomoContainer');
  const loginView = document.getElementById('loginView');
  const leftSection = document.getElementById('leftSection');
  const responseSection = document.getElementById('responseSection');
  const interactionHistory = document.getElementById('interactionHistory');
  const leftGif = document.getElementById('leftSectionGif');
  const healthBarContainer = document.getElementById('healthBarContainer');
  
  // Transition from idle to happy
  transitionToState('happy');
  
  container.classList.add('playing');
  loginView.classList.remove('visible');
  leftSection.style.display = 'flex';
  responseSection.classList.add('visible');
  healthBarContainer.classList.add('visible');
  
  // Show interaction history and display greeting
  interactionHistory.style.display = 'flex';
  // Clear any demo content
  while (interactionHistory.firstChild) {
    interactionHistory.removeChild(interactionHistory.firstChild);
  }
  
  // Add greeting message
  if (greetingMessage) {
    const greetingItem = document.createElement('div');
    greetingItem.className = 'interaction-item';
    const greetingDisplay = document.createElement('div');
    greetingDisplay.className = 'response-display';
    greetingDisplay.textContent = '> ' + greetingMessage;
    greetingItem.appendChild(greetingDisplay);
    interactionHistory.appendChild(greetingItem);
  }
  
  // Update health bar with current health
  updateHealthBar(currentHealth);
  
  // Start ESP32 heartbeat when game starts
  startESP32Heartbeat();
}

// Handle user input
document.getElementById('userInput').addEventListener('keypress', async function(e) {
  if (e.key === 'Enter' && this.value.trim()) {
    const history = document.getElementById('interactionHistory');
    history.style.display = 'flex'; // Ensure visible
    
    const newInteraction = document.createElement('div');
    newInteraction.className = 'interaction-item';
    
    const userInput = document.createElement('div');
    userInput.className = 'user-input-display';
    userInput.textContent = '> ' + this.value;
    
    const response = document.createElement('div');
    response.className = 'response-display';
    
    // Start dot animation
    const animation = animateDots(response, (data) => {
      response.textContent = '> ' + data;
      // Auto scroll after response is displayed
      history.scrollTop = history.scrollHeight;
    });
    
    newInteraction.appendChild(userInput);
    newInteraction.appendChild(response);
    history.appendChild(newInteraction);
    
    const userText = this.value;
    this.value = '';
    
    // Auto scroll immediately after adding user input
    history.scrollTop = history.scrollHeight;
    
    // Fetch Gemini response
    (async () => {
      try {
        const res = await fetch('/api/gemini', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            input: userText,
            conversation_state: conversationState,
            username: currentUsername
          })
        });
        const data = await res.json();
        const geminiResponse = data.response || 'No response';
        
        // Update conversation state
        if (data.conversation_state) {
          conversationState = data.conversation_state;
        }
        
        // Show upload button only when explicitly requested
        const uploadContainer = document.getElementById('imageUploadContainer');
        if (data.show_upload) {
          uploadContainer.classList.add('visible');
        }
        
        // Hide upload button if user declined
        if (data.hide_upload) {
          uploadContainer.classList.remove('visible');
        }
        
        animation.stop(geminiResponse);
      } catch (err) {
        animation.stop(" ｢('◉⌓◉')ﾂ  Your question makes my head spin! ");
      }
    })();
    
    // Auto scroll to bottom
    history.scrollTop = history.scrollHeight;
  }
});

// Handle image upload
document.getElementById('imageUpload').addEventListener('change', async function(e) {
  if (e.target.files && e.target.files[0]) {
    const history = document.getElementById('interactionHistory');
    const newInteraction = document.createElement('div');
    newInteraction.className = 'interaction-item';
    
    const userInput = document.createElement('div');
    userInput.className = 'user-input-display';
    userInput.textContent = '> I can see it!';
    
    const response = document.createElement('div');
    response.className = 'response-display';
    
    // Start dot animation
    const animation = animateDots(response, (data) => {
      response.textContent = '> ' + data;
      // Auto scroll after response is displayed
      history.scrollTop = history.scrollHeight;
    });
    
    newInteraction.appendChild(userInput);
    newInteraction.appendChild(response);
    history.appendChild(newInteraction);
    
    // Auto scroll immediately after adding user input
    history.scrollTop = history.scrollHeight;
    
    // Upload the image
    const formData = new FormData();
    formData.append('image', e.target.files[0]);
    formData.append('username', currentUsername);
    
    try {
      const res = await fetch('/api/feed', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      animation.stop(data.response || 'No response');
      
      // Hide upload container immediately after successful upload
      const uploadContainer = document.getElementById('imageUploadContainer');
      uploadContainer.classList.remove('visible');
      
      // Check if currently sad and food is healthy
      const wasSad = currentMood === 'sad';
      const isHealthyFood = data.is_healthy_food || false;
      
      // Update health bar if health data is returned
      if (data.health !== undefined) {
        updateHealthBar(data.health);
      }
      
      // If was sad and food is healthy, temporarily go happy then back to sad
      if (wasSad && isHealthyFood && data.health <= 10) {
        // Transition to happy briefly
        transitionToState('happy');
        
        // After 3 seconds, transition back to sad
        setTimeout(() => {
          transitionToState('sad');
        }, 3000);
      }
    } catch (err) {
      animation.stop('Error uploading image');
      // Also hide upload container on error
      const uploadContainer = document.getElementById('imageUploadContainer');
      uploadContainer.classList.remove('visible');
    }
    
    // Reset file input
    e.target.value = '';
    
    // Reset conversation state after image upload
    conversationState = 'initial';
    
    // Auto scroll to bottom
    history.scrollTop = history.scrollHeight;
  }
});
