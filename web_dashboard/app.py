from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import os
import json
from datetime import datetime
import threading
import sys
sys.path.append('..')
from bot import EvilRedditBot

app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key = os.urandom(24)  # For session management

# Store bot instances
bots = {}

# Load config
def load_config():
    try:
        with open('../config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "reddit": {},
            "subreddits": [],
            "bot_actions": {
                "upvote": True,
                "comment": True,
                "response_message": ""
            },
            "ui": {
                "do_not_disturb": []
            }
        }

# Save config
def save_config(config):
    with open('../config.json', 'w') as f:
        json.dump(config, f, indent=4)

# Evil logger
def log_action(action, status="SUCCESS", details=""):
    timestamp = datetime.now().strftime("%H:%M:%S")
    return f"[{timestamp}] [{status}] {action} - {details}"

@app.route('/')
def index():
    config = load_config()
    return render_template('index.html', config=config)

@app.route('/api/set-target', methods=['POST'])
def set_target():
    data = request.json
    config = load_config()
    
    subreddit = data.get('subreddit', '').strip()
    if not subreddit:
        return jsonify({
            'status': 'error',
            'message': 'Subreddit name is required',
            'log': log_action("Set Target", "ERROR", "Empty subreddit name")
        }), 400

    config['subreddits'] = [subreddit]
    save_config(config)
    
    # Get bot instance
    bot_id = session.get('bot_id')
    if bot_id and bot_id in bots:
        bots[bot_id].config['subreddits'] = [subreddit]
        
    response = {
        'status': 'success',
        'message': f'Target set to r/{subreddit}',
        'log': log_action("Set Target", "SUCCESS", f"Infiltrating r/{subreddit}")
    }
    
    # Emit update via WebSocket
    socketio.emit('bot_update', {
        'type': 'target_set',
        'data': {'subreddit': subreddit}
    })
    
    return jsonify(response)

@app.route('/api/update-dnd', methods=['POST'])
def update_dnd():
    data = request.json
    config = load_config()
    
    usernames = data.get('usernames', [])
    if isinstance(usernames, str):
        usernames = [u.strip() for u in usernames.split('\n') if u.strip()]
    
    config['ui']['do_not_disturb'] = usernames
    save_config(config)
    
    # Get bot instance
    bot_id = session.get('bot_id')
    if bot_id and bot_id in bots:
        bots[bot_id].config['ui']['do_not_disturb'] = usernames
        
    response = {
        'status': 'success',
        'message': f'Protected {len(usernames)} users from the darkness',
        'log': log_action("Update DND", "SUCCESS", f"Protected users: {', '.join(usernames[:3])}...")
    }
    
    # Emit update via WebSocket
    socketio.emit('bot_update', {
        'type': 'dnd_updated',
        'data': {'protected_count': len(usernames)}
    })
    
    return jsonify(response)

@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    data = request.json
    config = load_config()
    
    required_fields = ['username', 'password', 'client_id', 'client_secret']
    missing_fields = [f for f in required_fields if not data.get(f)]
    
    if missing_fields:
        return jsonify({
            'status': 'error',
            'message': f'Missing required fields: {", ".join(missing_fields)}',
            'log': log_action("Authentication", "ERROR", "Incomplete dark protocol credentials")
        }), 400

    # Store Reddit credentials
    config['reddit'] = {
        'username': data['username'],
        'password': data['password'],
        'client_id': data['client_id'],
        'client_secret': data['client_secret'],
        'user_agent': 'EvilRedditBot/1.0'
    }
    save_config(config)
    
    session['authenticated'] = True
    session['username'] = data['username']
    
    # Create new bot instance
    bot_id = f"bot_{data['username']}"
    if bot_id not in bots:
        bots[bot_id] = EvilRedditBot()
        bots[bot_id].config['reddit'] = {
            'username': data['username'],
            'password': data['password'],
            'client_id': data['client_id'],
            'client_secret': data['client_secret'],
            'user_agent': 'EvilRedditBot/1.0'
        }
        
        # Start bot in a separate thread
        def run_bot():
            try:
                bots[bot_id].run()
            except Exception as e:
                print(f"Bot error: {str(e)}")
                
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
    
    session['bot_id'] = bot_id
    
    response = {
        'status': 'success',
        'message': 'Dark protocol initialized successfully',
        'log': log_action("Authentication", "SUCCESS", f"Evil powers granted to {data['username']}")
    }
    
    # Emit update via WebSocket
    socketio.emit('bot_update', {
        'type': 'auth_success',
        'data': {'username': data['username']}
    })
    
    return jsonify(response)

@app.route('/api/status')
def get_status():
    config = load_config()
    return jsonify({
        'status': 'success',
        'data': {
            'subreddit': config['subreddits'][0] if config['subreddits'] else None,
            'protected_users': len(config['ui'].get('do_not_disturb', [])),
            'authenticated': session.get('authenticated', False),
            'username': session.get('username', None)
        }
    })

@app.route('/api/stop-bot', methods=['POST'])
def stop_bot():
    bot_id = session.get('bot_id')
    if bot_id and bot_id in bots:
        bots[bot_id].stop()  # Assuming your EvilRedditBot has a stop method
        response = {
            'status': 'success',
            'message': 'Bot has been stopped successfully',
            'log': log_action("Stop Bot", "SUCCESS", f"Stopped bot for {session['username']}")
        }
        
        # Emit update via WebSocket
        socketio.emit('bot_update', {
            'type': 'bot_stopped',
            'data': {'username': session['username']}
        })
        
        return jsonify(response)
    else:
        return jsonify({
            'status': 'error',
            'message': 'No active bot found',
            'log': log_action("Stop Bot", "ERROR", "No active bot to stop")
        }), 400

@app.route('/api/get-logs', methods=['GET'])
def get_logs():
    # Assuming you have a log file or a logging mechanism
    try:
        with open('../logs.txt', 'r') as log_file:
            logs = log_file.readlines()
        return jsonify({
            'status': 'success',
            'logs': logs
        })
    except FileNotFoundError:
        return jsonify({
            'status': 'error',
            'message': 'Log file not found'
        }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'An internal error occurred',
        'log': log_action("Internal Error", "ERROR", str(error))
    }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Resource not found',
        'log': log_action("Not Found", "ERROR", str(error))
    }), 404

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    bot_id = session.get('bot_id')
    if bot_id and bot_id in bots:
        emit('bot_update', {
            'type': 'status',
            'data': {
                'active': True,
                'username': bots[bot_id].config['reddit'].get('username')
            }
        })

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    # Ensure config exists
    if not os.path.exists('../config.json'):
        save_config(load_config())
    
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)