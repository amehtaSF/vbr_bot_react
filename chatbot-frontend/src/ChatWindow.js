import React, { useState, useEffect } from 'react';
import InputWidget from './InputWidget';
import MessageList from './MessageList';
import axios from 'axios';

function ChatWindow() {
    const [messages, setMessages] = useState([]);
    const [widgetType, setWidgetType] = useState('text');
    const [widgetConfig, setWidgetConfig] = useState({});
    const [jwtToken, setJwtToken] = useState(null);

    // Get the API URL from the environment variable
    const API_URL = process.env.REACT_APP_FLASK_API_URL;

    // Login and retrieve the JWT token when the component is mounted
    useEffect(() => {
        const login = async () => {
            console.log('Logging in...', API_URL);
            try {
                const response = await axios.post(`${API_URL}/api/login`);
                const token = response.data.access_token;
                setJwtToken(token); // Store the JWT token in state
            } catch (error) {
                console.error('Login failed', error);
            }
        };

        login(); // Call the login function when the component mounts
    }, [API_URL]);

    // Function to send a message to the chat API
    const sendMessage = async (userMessage) => {
        if (!jwtToken) {
            console.error('JWT token not available');
            return;
        }

        try {
            const response = await axios.post(
                `${API_URL}/api/chat`,
                { user_message: userMessage, 
                    widget_type: widgetType,
                    widget_config: widgetConfig },
                {
                    headers: {
                        Authorization: `Bearer ${jwtToken}` // Include JWT token in Authorization header
                    }
                }
            );

            const botMessage = response.data.bot_message;
            const newWidgetType = response.data.widget_type || 'text'; // Retrieve new widget type from API
            const newWidgetConfig = response.data.widget_config || {}; // Retrieve new widget config from API

            // Update the message history and widget type/config
            setMessages((prevMessages) => [
                ...prevMessages,
                { sender: 'user', text: userMessage },
                { sender: 'bot', text: botMessage },
            ]);
            setWidgetType(newWidgetType); // Update the widget type based on API response
            setWidgetConfig(newWidgetConfig); // Update the widget configuration based on API response
        } catch (error) {
            console.error('Error sending message:', error);
        }
    };

    return (
        <div className="chat-window">
            <MessageList messages={messages} />
            <InputWidget widgetType={widgetType} onSend={sendMessage} widgetConfig={widgetConfig} />
        </div>
    );
}

export default ChatWindow;