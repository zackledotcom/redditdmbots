// DOM Elements
const activityFeed = document.getElementById('activity-feed');
const botForm = document.getElementById('bot-config');
const startButton = document.getElementById('start-bot');
const stopButton = document.getElementById('stop-bot');
const botStatus = document.querySelector('.bot-status');
const messagesCount = document.getElementById('messages-count');
const subredditsCount = document.getElementById('subreddits-count');

// Activity Feed Management
function addActivity(activity) {
    const activityElement = document.createElement('div');
    activityElement.className = 'bg-[#272729] p-3 rounded border border-[#343536]';
    
    const timestamp = new Date().toLocaleTimeString();
    const icon = getActivityIcon(activity.type);
    
    activityElement.innerHTML = `
        <div class="flex items-center justify-between mb-1">
            <div class="flex items-center space-x-2">
                <i class="${icon} text-[#FF4500]"></i>
                <span class="text-sm font-medium">${activity.title}</span>
            </div>
            <span class="text-xs text-[#818384]">${timestamp}</span>
        </div>
        <p class="text-sm text-[#D7DADC] opacity-90">${activity.description}</p>
    `;
    
    activityFeed.prepend(activityElement);
}

function getActivityIcon(type) {
    const icons = {
        'auth': 'fa-solid fa-key',
        'comment': 'fa-regular fa-comment',
        'upvote': 'fa-solid fa-arrow-up',
        'error': 'fa-solid fa-triangle-exclamation',
        'start': 'fa-solid fa-play',
        'stop': 'fa-solid fa-stop'
    };
    return icons[type] || 'fa-regular fa-circle';
}

// Form Handling
botForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(botForm);
    const botConfig = {
        subreddit: formData.get('subreddit'),
        username: formData.get('username'),
        password: formData.get('password'),
        client_id: formData.get('client_id'),
        client_secret: formData.get('client_secret')
    };

    try {
        const response = await fetch('/api/authenticate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(botConfig)
        });

        const result = await response.json();
        
        if (result.status === 'success') {
            addActivity({
                type: 'auth',
                title: 'Authentication Successful',
                description: result.message
            });
            updateBotStatus(true);
        } else {
            addActivity({
                type: 'error',
                title: 'Authentication Failed',
                description: result.message
            });
        }
    } catch (error) {
        addActivity({
            type: 'error',
            title: 'Network Error',
            description: 'Failed to connect to server'
        });
    }
});

// Bot Controls
startButton.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/start', {method: 'POST'});
        const result = await response.json();
        
        if (result.status === 'success') {
            addActivity({
                type: 'start',
                title: 'Bot Started',
                description: result.message
            });
            updateBotStatus(true);
        }
    } catch (error) {
        addActivity({
            type: 'error',
            title: 'Start Failed',
            description: error.message
        });
    }
});

stopButton.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/stop', {method: 'POST'});
        const result = await response.json();
        
        if (result.status === 'success') {
            addActivity({
                type: 'stop',
                title: 'Bot Stopped',
                description: result.message
            });
            updateBotStatus(false);
        }
    } catch (error) {
        addActivity({
            type: 'error',
            title: 'Stop Failed',
            description: error.message
        });
    }
});

// Status Updates
function updateBotStatus(isActive) {
    const statusIcon = botStatus.querySelector('i');
    const statusText = botStatus.querySelector('span');
    
    if (isActive) {
        statusIcon.className = 'fa-solid fa-circle text-green-500 mr-2';
        statusText.textContent = 'Active';
    } else {
        statusIcon.className = 'fa-solid fa-circle text-gray-500 mr-2';
        statusText.textContent = 'Inactive';
    }
}

// Poll for updates
setInterval(async () => {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        if (status.status === 'success') {
            messagesCount.textContent = status.data.messages || 0;
            subredditsCount.textContent = status.data.subreddits || 0;
            updateBotStatus(status.data.isActive);
        }
    } catch (error) {
        console.error('Status update failed:', error);
    }
}, 5000);