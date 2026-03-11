
import os
import sys
import json
import time
import logging
import threading
import http.server
import socketserver
from urllib.parse import urlparse
from datetime import datetime

PORT = 54779
HISTORY_FILE = 'chat_history.json'
USERS_FILE = 'users.json'
LOG_FILE = 'chat_server.log'
CLEANUP_INTERVAL = 3 * 60 * 60
LOG_CLEANUP_INTERVAL = 24 * 60 * 60

# 管理员账户
ADMIN_USERNAME = 'happygray110'
ADMIN_PASSWORD = 'Ds140301'

HTML_CONTENT = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>chatbox - HGSpaced/happygray110</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg-primary: #313338;
            --bg-secondary: #2b2d31;
            --bg-tertiary: #202225;
            --bg-accent: #5865F2;
            --text-primary: #ffffff;
            --text-secondary: #b9bbbe;
            --text-muted: #72767d;
            --border-color: #00000040;
            --channel-name: #949ba4;
            --header-height: 48px;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #1a1c23 0%, #2d303a 100%);
            color: var(--text-primary);
            height: 100vh;
            overflow: hidden;
        }

        .app-container {
            display: flex;
            height: 100vh;
            width: 100%;
        }

        .server-list {
            width: 60px;
            background: var(--bg-primary);
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 10px;
            gap: 8px;
            flex-shrink: 0;
        }

        .server-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, #5865F2, #7289da);
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: bold;
        }

        .server-icon:hover {
            transform: scale(1.1);
            background: linear-gradient(135deg, #7289da, #5865F2);
        }

        .server-icon.active {
            background: linear-gradient(135deg, #5865F2, #7289da);
            box-shadow: 0 0 0 3px #ffffff40;
        }

        .channel-list {
            width: 240px;
            background: var(--bg-primary);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }

        .channel-header {
            height: var(--header-height);
            padding: 0 16px;
            display: flex;
            align-items: center;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
        }

        .channel-header h2 {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .channel-category {
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-primary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 8px;
        }

        .channel-item {
            padding: 6px 16px;
            margin: 2px 8px;
            border-radius: 4px;
            color: var(--channel-name);
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .channel-item:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        .channel-item.active {
            background: var(--bg-secondary);
            color: var(--text-primary);
            font-weight: 500;
        }

        .channel-item::before {
            content: '#';
            font-size: 14px;
        }

        .admin-panel {
            padding: 8px 16px;
            margin-top: 8px;
            border-top: 1px solid var(--border-color);
        }

        .admin-btn {
            width: 100%;
            padding: 8px;
            margin-bottom: 4px;
            border-radius: 4px;
            border: none;
            background: var(--bg-primary);
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s ease;
            text-align: left;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .admin-btn:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        .admin-btn.danger:hover {
            background: #f0474730;
            color: #f04747;
        }

        .online-users-list {
            padding: 8px 16px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .online-user {
            padding: 6px 12px;
            margin: 2px 0;
            border-radius: 4px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }

        .online-user:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        .online-user::before {
            content: '●';
            color: var(--bg-accent);
            font-size: 10px;
        }

        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg-tertiary);
            position: relative;
        }

        .chat-header {
            height: var(--header-height);
            padding: 0 24px;
            display: flex;
            align-items: center;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            backdrop-filter: blur(20px);
        }

        .chat-header h1 {
            font-size: 20px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .chat-header .channel-desc {
            margin-left: 12px;
            font-size: 14px;
            color: var(--text-muted);
        }

        .chat-history {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
            scroll-behavior: smooth;
        }

        .chat-message {
            display: flex;
            gap: 16px;
            padding: 8px 0;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            flex-shrink: 0;
            background: linear-gradient(135deg, #5865F2, #7289da);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: bold;
            color: white;
        }

        .message-content {
            flex: 1;
        }

        .message-header {
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin-bottom: 4px;
        }

        .message-username {
            font-weight: 600;
            color: var(--text-primary);
            font-size: 15px;
            cursor: pointer;
        }

        .message-username:hover {
            text-decoration: underline;
        }

        .message-meta {
            font-size: 13px;
            color: var(--text-muted);
        }

        .message-text {
            font-size: 15px;
            line-height: 1.5;
            color: var(--text-primary);
            word-wrap: break-word;
        }

        .message-text a {
            color: #00b0f4;
            text-decoration: none;
        }

        .message-text a:hover {
            text-decoration: underline;
        }

        .chat-input-area {
            padding: 24px;
            background: var(--bg-tertiary);
        }

        .input-wrapper {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 12px 16px;
            display: flex;
            gap: 12px;
            border: 1px solid var(--border-color);
            transition: all 0.2s ease;
        }

        .input-wrapper:focus-within {
            border-color: var(--bg-accent);
            box-shadow: 0 0 0 3px var(--bg-accent)30;
        }

        .emoji-btn {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: all 0.2s ease;
        }

        .emoji-btn:hover {
            background: var(--bg-primary);
            color: var(--text-primary);
        }

        #message-input {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text-primary);
            font-size: 15px;
            line-height: 1.5;
            resize: none;
            max-height: 200px;
            font-family: inherit;
        }

        #message-input::placeholder {
            color: var(--text-muted);
        }

        #message-input:focus {
            outline: none;
        }

        #send-btn {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border: none;
            background: var(--bg-accent);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            transition: all 0.2s ease;
            flex-shrink: 0;
        }

        #send-btn:hover {
            background: #4752c4;
            transform: scale(1.05);
        }

        #send-btn:active {
            transform: scale(0.95);
        }

        .login-screen {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            background: linear-gradient(135deg, #1a1c23 0%, #2d303a 100%);
        }

        .login-container {
            background: var(--bg-secondary);
            padding: 48px;
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-color);
            text-align: center;
            min-width: 400px;
            max-width: 500px;
        }

        .login-container h1 {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            color: var(--text-primary);
        }

        .login-container .subtitle {
            color: var(--text-secondary);
            font-size: 14px;
            margin-bottom: 32px;
        }

        .input-group {
            margin-bottom: 24px;
            text-align: left;
        }

        .input-group label {
            display: block;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
        }

        .input-group input {
            width: 100%;
            padding: 12px 16px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: var(--bg-primary);
            color: var(--text-primary);
            font-size: 15px;
            transition: all 0.2s ease;
        }

        .input-group input:focus {
            outline: none;
            border-color: var(--bg-accent);
            box-shadow: 0 0 0 3px var(--bg-accent)30;
        }

        .btn {
            width: 100%;
            padding: 12px 24px;
            border-radius: 8px;
            border: none;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-primary {
            background: var(--bg-accent);
            color: white;
        }

        .btn-primary:hover {
            background: #4752c4;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(88, 101, 242, 0.4);
        }

        .btn-primary:active {
            transform: translateY(0);
        }

        .btn-secondary {
            background: var(--bg-primary);
            color: var(--text-primary);
            margin-top: 12px;
        }

        .btn-secondary:hover {
            background: #3a3d42;
        }

        .hint {
            margin-top: 16px;
            font-size: 13px;
            color: var(--text-muted);
        }

        .hidden {
            display: none !important;
        }

        .typing-indicator {
            padding: 12px 24px;
            color: var(--text-muted);
            font-size: 13px;
            font-style: italic;
        }

        .typing-indicator span {
            animation: typing 1.4s infinite ease-in-out both;
        }

        .typing-indicator span:nth-child(1) {
            animation-delay: -0.32s;
        }

        .typing-indicator span:nth-child(2) {
            animation-delay: -0.16s;
        }

        @keyframes typing {
            0%, 80%, 100% {
                opacity: 0;
            }
            40% {
                opacity: 1;
            }
        }

        @media (max-width: 768px) {
            .server-list {
                display: none;
            }

            .channel-list {
                display: none;
            }

            .login-container {
                min-width: auto;
                padding: 24px;
            }

            .chat-message {
                padding: 4px 0;
            }

            .avatar {
                width: 36px;
                height: 36px;
                font-size: 16px;
            }

            .message-text {
                font-size: 14px;
            }

            .chat-input-area {
                padding: 12px;
            }

            .input-wrapper {
                padding: 8px 12px;
            }

            .emoji-btn {
                width: 28px;
                height: 28px;
                font-size: 16px;
            }

            #send-btn {
                width: 32px;
                height: 32px;
                font-size: 14px;
            }

            .chat-header {
                padding: 0 16px;
            }

            .chat-header h1 {
                font-size: 18px;
            }

            .chat-header .channel-desc {
                font-size: 13px;
            }

            .chat-history {
                padding: 16px;
            }

            .admin-panel {
                display: none !important;
            }
        }
    </style>
</head>
<body>
    <div id="login-screen" class="login-screen">
        <div class="login-container">
            <h1 id="login-title">登录</h1>
            <p class="subtitle" id="login-subtitle">欢迎来到 chatbox</p>
            
            <div id="login-form">
                <div class="input-group">
                    <label for="login-username">用户名</label>
                    <input type="text" id="login-username" placeholder="输入用户名" maxlength="20">
                </div>
                <div class="input-group">
                    <label for="login-password">密码</label>
                    <input type="password" id="login-password" placeholder="输入密码">
                </div>
                <button id="login-btn" class="btn btn-primary">登录</button>
                <p class="hint">用户名将保存在浏览器Cookie中，下次自动填充</p>
                <button id="switch-to-register" class="btn btn-secondary" style="margin-top: 12px;">没有账户？注册一个</button>
            </div>
            
            <div id="register-form" class="hidden">
                <div class="input-group">
                    <label for="register-username">用户名</label>
                    <input type="text" id="register-username" placeholder="输入用户名" maxlength="20">
                </div>
                <div class="input-group">
                    <label for="register-password">密码</label>
                    <input type="password" id="register-password" placeholder="输入密码">
                </div>
                <div class="input-group">
                    <label for="register-confirm-password">确认密码</label>
                    <input type="password" id="register-confirm-password" placeholder="确认密码">
                </div>
                <button id="register-btn" class="btn btn-primary">注册</button>
                <button id="switch-to-login" class="btn btn-secondary">已有账号？去登录</button>
            </div>
        </div>
    </div>

    <div id="chat-screen" class="app-container hidden">
        <div class="server-list">
            <div class="server-icon active" onclick="switchToChat()">C</div>
        </div>

        <div class="channel-list">
            <div class="channel-header">
                <h2 id="channel-title">聊天室</h2>
            </div>
            <div class="channel-category">文本频道</div>
            <div class="channel-item active" onclick="switchToChat()"># 通用</div>
            <div class="channel-category">在线玩家 (<span id="online-count">0</span>)</div>
            <div id="online-users" class="online-users-list">
            </div>
            <div id="admin-panel" class="admin-panel hidden">
                <div class="channel-category" style="margin-top: 0; font-size: 11px;">管理员面板</div>
                <button class="admin-btn" onclick="clearChatHistory()">
                    <span>🗑️</span> 清空聊天记录
                </button>
                <button class="admin-btn danger" onclick="toggleMute()">
                    <span>🔇</span> <span id="mute-btn-text">禁言</span>
                </button>
                <button class="admin-btn" onclick="sendToAll()">
                    <span>📢</span> @所有人
                </button>
            </div>
        </div>

        <div class="chat-area" id="chat-area">
            <div class="chat-header">
                <h1 id="chat-title">通用</h1>
                <span class="channel-desc" id="chat-desc">欢迎来到聊天室！</span>
            </div>

            <div id="chat-history" class="chat-history">
            </div>

            <div id="typing-indicator" class="typing-indicator hidden">
                <span>...</span>
            </div>

            <div class="chat-input-area">
                <div class="input-wrapper">
                    <button class="emoji-btn" id="emoji-btn">😊</button>
                    <textarea id="message-input" placeholder="发送消息..." rows="1"></textarea>
                    <button id="send-btn">➤</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const COOKIE_NAME = 'chat_username';
        const CLEANUP_INTERVAL = 3 * 60 * 60 * 1000;

        let username = '';
        let chatHistory = [];
        let onlineUsers = new Set();
        let isMuted = false;
        let isAdmin = false;

        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) {
                return parts.pop().split(';').shift();
            }
            return null;
        }

        function setCookie(name, value, days = 30) {
            const expires = new Date();
            expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
            document.cookie = `${name}=${encodeURIComponent(value)};expires=${expires.toUTCString()};path=/`;
        }

        function updateOnlineUsers(users) {
            const onlineUsersList = document.getElementById('online-users');
            const onlineCount = document.getElementById('online-count');
            
            onlineUsersList.innerHTML = '';
            onlineUsers.clear();
            
            users.forEach(user => {
                onlineUsers.add(user);
                const userDiv = document.createElement('div');
                userDiv.className = 'online-user';
                userDiv.textContent = user;
                onlineUsersList.appendChild(userDiv);
            });
            
            onlineCount.textContent = users.length;
        }

        function loadHistory() {
            fetch('/history')
                .then(response => response.json())
                .then(data => {
                    const newHistory = data.history;

                    if (newHistory.length > chatHistory.length) {
                        const newMessages = newHistory.slice(chatHistory.length);
                        appendMessages(newMessages);
                    } else if (newHistory.length < chatHistory.length) {
                        chatHistory = newHistory;
                        renderHistory();
                    }

                    chatHistory = newHistory;
                })
                .catch(error => {
                    console.error('加载聊天记录失败:', error);
                });
        }

        function loadOnlineUsers() {
            fetch('/online')
                .then(response => response.json())
                .then(data => {
                    updateOnlineUsers(data.users);
                })
                .catch(error => {
                    console.error('加载在线用户失败:', error);
                });
        }

        function renderHistory() {
            const chatHistoryDiv = document.getElementById('chat-history');
            chatHistoryDiv.innerHTML = '';

            chatHistory.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'chat-message';

                const escapedUsername = escapeHtml(msg.username);
                const escapedText = escapeHtml(msg.text);
                const timestamp = formatTime(msg.timestamp);

                messageDiv.innerHTML = `
                    <div class="avatar">${msg.username.charAt(0).toUpperCase()}</div>
                    <div class="message-content">
                        <div class="message-header">
                            <span class="message-username">${escapedUsername}</span>
                            <span class="message-meta">${timestamp}</span>
                        </div>
                        <div class="message-text">${escapedText}</div>
                    </div>
                `;

                chatHistoryDiv.appendChild(messageDiv);
            });

            scrollToBottom();
        }

        function appendMessages(messages) {
            const chatHistoryDiv = document.getElementById('chat-history');

            messages.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'chat-message';

                const escapedUsername = escapeHtml(msg.username);
                const escapedText = escapeHtml(msg.text);
                const timestamp = formatTime(msg.timestamp);

                messageDiv.innerHTML = `
                    <div class="avatar">${msg.username.charAt(0).toUpperCase()}</div>
                    <div class="message-content">
                        <div class="message-header">
                            <span class="message-username">${escapedUsername}</span>
                            <span class="message-meta">${timestamp}</span>
                        </div>
                        <div class="message-text">${escapedText}</div>
                    </div>
                `;

                chatHistoryDiv.appendChild(messageDiv);
            });

            scrollToBottom();
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function formatTime(timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            const msgDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());

            if (msgDate.getTime() === today.getTime()) {
                return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
            } else if (msgDate.getTime() > today.getTime() - 86400000) {
                return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
            } else {
                return date.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
            }
        }

        function scrollToBottom() {
            const chatHistoryDiv = document.getElementById('chat-history');
            chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
        }

        function sendMessage() {
            const messageInput = document.getElementById('message-input');
            const text = messageInput.value.trim();

            if (!text) {
                alert('请输入消息内容');
                return;
            }

            if (!username) {
                alert('请先登录');
                return;
            }

            console.log('发送消息:', { username: username, text: text });

            fetch('/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    text: text
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('发送响应:', data);
                if (data.status === 'success') {
                    messageInput.value = '';
                    loadHistory();
                } else {
                    alert('发送失败: ' + data.message);
                }
            })
            .catch(error => {
                console.error('发送消息失败:', error);
                alert('发送失败，请检查网络连接');
            });
        }

        function showChatScreen() {
            document.getElementById('login-screen').classList.add('hidden');
            document.getElementById('chat-screen').classList.remove('hidden');
            
            if (username === ADMIN_USERNAME) {
                isAdmin = true;
                document.getElementById('admin-panel').classList.remove('hidden');
            }
            
            loadHistory();
            loadOnlineUsers();
            setInterval(loadHistory, 3000);
            setInterval(loadOnlineUsers, 5000);
        }

        function checkCleanup() {
            const now = new Date();
            const lastCleanup = localStorage.getItem('last_cleanup');

            if (!lastCleanup || (now.getTime() - new Date(lastCleanup).getTime() > CLEANUP_INTERVAL)) {
                localStorage.setItem('last_cleanup', now.toISOString());
                loadHistory();
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            const loginUsernameInput = document.getElementById('login-username');
            const registerUsernameInput = document.getElementById('register-username');

            loginUsernameInput.focus();

            document.getElementById('login-btn').addEventListener('click', () => {
                const inputUsername = loginUsernameInput.value.trim();
                const inputPassword = document.getElementById('login-password').value;

                if (!inputUsername) {
                    alert('请输入用户名');
                    return;
                }

                if (!inputPassword) {
                    alert('请输入密码');
                    return;
                }

                fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username: inputUsername,
                        password: inputPassword
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        username = inputUsername;
                        showChatScreen();
                    } else {
                        alert('登录失败: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('登录失败:', error);
                    alert('登录失败，请检查网络连接');
                });
            });

            document.getElementById('register-btn').addEventListener('click', () => {
                const inputUsername = registerUsernameInput.value.trim();
                const inputPassword = document.getElementById('register-password').value;
                const confirmPassword = document.getElementById('register-confirm-password').value;

                if (!inputUsername) {
                    alert('请输入用户名');
                    return;
                }

                if (!inputPassword) {
                    alert('请输入密码');
                    return;
                }

                if (!confirmPassword) {
                    alert('请确认密码');
                    return;
                }

                if (inputPassword !== confirmPassword) {
                    alert('两次输入的密码不一致');
                    return;
                }

                fetch('/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username: inputUsername,
                        password: inputPassword
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        username = inputUsername;
                        showChatScreen();
                    } else {
                        alert('注册失败: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('注册失败:', error);
                    alert('注册失败，请检查网络连接');
                });
            });

            document.getElementById('switch-to-login').addEventListener('click', () => {
                document.getElementById('register-form').classList.add('hidden');
                document.getElementById('login-form').classList.remove('hidden');
                document.getElementById('login-title').textContent = '登录';
                document.getElementById('login-subtitle').textContent = '欢迎来到 chatbox';
                loginUsernameInput.focus();
            });

            document.getElementById('switch-to-register').addEventListener('click', () => {
                document.getElementById('login-form').classList.add('hidden');
                document.getElementById('register-form').classList.remove('hidden');
                document.getElementById('login-title').textContent = '注册';
                document.getElementById('login-subtitle').textContent = '创建新账户';
                registerUsernameInput.focus();
            });

            loginUsernameInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    document.getElementById('login-btn').click();
                }
            });

            document.getElementById('login-password').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    document.getElementById('login-btn').click();
                }
            });

            registerUsernameInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    document.getElementById('register-btn').click();
                }
            });

            document.getElementById('register-password').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    document.getElementById('register-btn').click();
                }
            });

            document.getElementById('register-confirm-password').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    document.getElementById('register-btn').click();
                }
            });

            document.getElementById('send-btn').addEventListener('click', sendMessage);

            const messageInput = document.getElementById('message-input');
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });

            messageInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 200) + 'px';
            });

            checkCleanup();
            setInterval(checkCleanup, 60000);

            document.addEventListener('keydown', (e) => {
                if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I') || 
                    (e.ctrlKey && e.shiftKey && e.key === 'J') || 
                    (e.ctrlKey && e.key === 'U')) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            });

            document.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        function switchToChat() {
            document.getElementById('chat-title').textContent = '通用';
            document.getElementById('chat-desc').textContent = '欢迎来到聊天室！';
            document.getElementById('channel-title').textContent = '聊天室';
        }

        function clearChatHistory() {
            if (!isAdmin) return;
            
            if (!confirm('确定要清空所有聊天记录吗？此操作不可恢复！')) {
                return;
            }

            fetch('/admin/clear_history', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    chatHistory = [];
                    renderHistory();
                    alert('聊天记录已清空');
                } else {
                    alert('操作失败: ' + data.message);
                }
            })
            .catch(error => {
                console.error('清空聊天记录失败:', error);
                alert('操作失败，请检查网络连接');
            });
        }

        function toggleMute() {
            if (!isAdmin) return;

            isMuted = !isMuted;
            const muteBtnText = document.getElementById('mute-btn-text');
            
            if (isMuted) {
                muteBtnText.textContent = '解除禁言';
                document.querySelector('.admin-btn.danger').style.backgroundColor = '#f0474730';
                document.querySelector('.admin-btn.danger').style.color = '#f04747';
            } else {
                muteBtnText.textContent = '禁言';
                document.querySelector('.admin-btn.danger').style.backgroundColor = '';
                document.querySelector('.admin-btn.danger').style.color = '';
            }

            fetch('/admin/toggle_mute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    muted: isMuted
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status !== 'success') {
                    alert('操作失败: ' + data.message);
                }
            })
            .catch(error => {
                console.error('禁言操作失败:', error);
            });
        }

        function sendToAll() {
            if (!isAdmin) return;

            const message = prompt('请输入要发送给所有人的消息:');
            if (!message) return;

            fetch('/admin/send_to_all', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    message: message
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    loadHistory();
                    alert('消息已发送给所有人');
                } else {
                    alert('操作失败: ' + data.message);
                }
            })
            .catch(error => {
                console.error('发送消息失败:', error);
                alert('操作失败，请检查网络连接');
            });
        }
    </script>
</body>
</html>
'''

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

chat_history = []
online_users = set()
users = {}

def load_history():
    global chat_history
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                chat_history = json.load(f)
            logging.info(f"加载聊天记录: {len(chat_history)} 条")
        except Exception as e:
            logging.error(f"加载聊天记录失败: {e}")
            chat_history = []

def load_users():
    global users
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
            logging.info(f"加载用户数据: {len(users)} 个用户")
        except Exception as e:
            logging.error(f"加载用户数据失败: {e}")
            users = {}
    else:
        users = {ADMIN_USERNAME: ADMIN_PASSWORD}

def save_history():
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"保存聊天记录失败: {e}")

def save_users():
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"保存用户数据失败: {e}")

def cleanup_history():
    global chat_history
    while True:
        time.sleep(CLEANUP_INTERVAL)
        chat_history = []
        save_history()
        logging.info("聊天记录已清除（3小时周期）")

def cleanup_log():
    while True:
        time.sleep(LOG_CLEANUP_INTERVAL)
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                if len(lines) > 1000:
                    with open(LOG_FILE, 'w', encoding='utf-8') as f:
                        f.writelines(lines[-1000:])
                logging.info("日志文件已清理")
        except Exception as e:
            logging.error(f"清理日志失败: {e}")

def update_online_users():
    global online_users
    while True:
        time.sleep(5)
        online_users = set()
        for msg in chat_history:
            online_users.add(msg['username'])

class ChatHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logging.info(f"{self.address_string()} - {format % args}")

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/history':
            self.send_json_response({'history': chat_history})
        elif parsed_path.path == '/online':
            self.send_json_response({'users': list(online_users)})
        elif parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/send':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            message = json.loads(post_data.decode())

            username = message.get('username', '匿名')
            text = message.get('text', '')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            chat_entry = {
                'username': username,
                'text': text,
                'timestamp': timestamp
            }
            chat_history.append(chat_entry)
            save_history()

            logging.info(f"消息: [{username}] {text}")
            self.send_json_response({'status': 'success', 'message': chat_entry})
        
        elif self.path == '/login':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())

            input_username = data.get('username', '')
            input_password = data.get('password', '')

            if input_username in users and users[input_username] == input_password:
                self.send_json_response({'status': 'success', 'message': '登录成功'})
            else:
                self.send_json_response({'status': 'failed', 'message': '用户名或密码错误'})
        
        elif self.path == '/register':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())

            input_username = data.get('username', '')
            input_password = data.get('password', '')

            if not input_username or not input_password:
                self.send_json_response({'status': 'failed', 'message': '用户名和密码不能为空'})
            elif len(input_password) < 8:
                self.send_json_response({'status': 'failed', 'message': '密码长度至少8位'})
            elif not any(c.isalpha() for c in input_password) or not any(c.isdigit() for c in input_password):
                self.send_json_response({'status': 'failed', 'message': '密码必须包含字母和数字'})
            elif input_username in users:
                self.send_json_response({'status': 'failed', 'message': '用户名已存在'})
            elif input_password in users.values():
                self.send_json_response({'status': 'failed', 'message': '该密码已被使用，请更换密码'})
            else:
                users[input_username] = input_password
                save_users()
                self.send_json_response({'status': 'success', 'message': '注册成功'})
        
        elif self.path == '/admin/clear_history':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())

            input_username = data.get('username', '')

            if input_username == ADMIN_USERNAME:
                chat_history.clear()
                save_history()
                self.send_json_response({'status': 'success', 'message': '聊天记录已清空'})
            else:
                self.send_json_response({'status': 'failed', 'message': '无权限'})
        
        elif self.path == '/admin/toggle_mute':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())

            input_username = data.get('username', '')
            muted = data.get('muted', False)

            if input_username == ADMIN_USERNAME:
                self.send_json_response({'status': 'success', 'message': f'已{"禁言" if muted else "解除禁言"}'})
            else:
                self.send_json_response({'status': 'failed', 'message': '无权限'})
        
        elif self.path == '/admin/send_to_all':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())

            input_username = data.get('username', '')
            message = data.get('message', '')

            if input_username == ADMIN_USERNAME:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                chat_entry = {
                    'username': '系统通知',
                    'text': f'📢 **@所有人**\n{message}',
                    'timestamp': timestamp
                }
                chat_history.append(chat_entry)
                save_history()
                self.send_json_response({'status': 'success', 'message': '消息已发送'})
            else:
                self.send_json_response({'status': 'failed', 'message': '无权限'})

        else:
            self.send_error(404)

def run_server():
    load_history()
    load_users()

    cleanup_thread = threading.Thread(target=cleanup_history, daemon=True)
    cleanup_thread.start()

    log_cleanup_thread = threading.Thread(target=cleanup_log, daemon=True)
    log_cleanup_thread.start()

    online_thread = threading.Thread(target=update_online_users, daemon=True)
    online_thread.start()

    with socketserver.TCPServer(("", PORT), ChatHandler) as httpd:
        logging.info(f"服务器启动在端口 {PORT}")
        logging.info(f"访问 http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == '__main__':
    try:
        run_server()
    except KeyboardInterrupt:
        logging.info("服务器已停止")
