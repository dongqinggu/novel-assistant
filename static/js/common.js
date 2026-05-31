/**
 * Common utilities for the novel assistant web interface
 */

// API helper
async function api(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    if (options.body && typeof options.body === 'object') {
        options.body = JSON.stringify(options.body);
    }
    
    const response = await fetch(endpoint, { ...defaultOptions, ...options });
    return response.json();
}

// Show message
function showMessage(message, type = 'info') {
    // Create or get message container
    let container = document.getElementById('message-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'message-container';
        container.style.cssText = `
            position: fixed;
            top: 60px;
            right: 340px;
            z-index: 1000;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }
    
    const msgEl = document.createElement('div');
    msgEl.className = type === 'error' ? 'error-message' : 'success-message';
    msgEl.textContent = message;
    msgEl.style.marginBottom = '8px';
    
    container.appendChild(msgEl);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        msgEl.remove();
    }, 3000);
}

// Format date
function formatDate(dateStr) {
    if (!dateStr) return '';
    return dateStr.substring(0, 10);
}

// Type display names
const TYPE_NAMES = {
    outline: '大纲',
    character: '人物',
    scene: '场景',
    plot: '剧情',
    callback: '伏笔',
    worldbuilding: '世界观',
    note: '笔记',
};

// Type icons
const TYPE_ICONS = {
    outline: '📋',
    character: '👤',
    scene: '📍',
    plot: '📖',
    callback: '🔗',
    worldbuilding: '🌍',
    note: '📝',
};

function getTypeName(type) {
    return TYPE_NAMES[type] || type;
}

function getTypeIcon(type) {
    return TYPE_ICONS[type] || '📄';
}
