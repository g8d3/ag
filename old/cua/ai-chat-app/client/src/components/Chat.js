import React, { useState, useEffect } from 'react';
import axios from 'axios';
import CodeExecutor from './CodeExecutor';

function Chat({ userId }) {
  const [message, setMessage] = useState('');
  const [chats, setChats] = useState([]);

  useEffect(() => {
    axios.get(`http://localhost:5000/chat/${userId}`).then((res) => setChats(res.data));
  }, [userId]);

  const sendMessage = async () => {
    const res = await axios.post('http://localhost:5000/chat', { userId, message });
    setChats([...chats, res.data]);
    setMessage('');
  };

  return (
    <div className="chat">
      <div id="chat-history">
        {chats.map((chat) => (
          <div key={chat.id}>
            <p><strong>You:</strong> {chat.message}</p>
            <p><strong>AI:</strong> {chat.response}</p>
            {chat.response.includes('```') && <CodeExecutor code={chat.response.match(/```(.*?)```/s)?.[1]} />}
          </div>
        ))}
      </div>
      <input id="chat-input" value={message} onChange={(e) => setMessage(e.target.value)} />
      <button id="send-button" onClick={sendMessage}>Send</button>
    </div>
  );
}

export default Chat;