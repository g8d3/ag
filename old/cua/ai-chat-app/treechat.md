Based on your app description, I'll implement a basic version of the **AI chat web app** with multi-user support, configurable API settings, chat history saved as a tree/graph, and code execution capability. I'll also include **Playwright headed tests** as requested. The implementation will use **React** for the frontend, **Node.js/Express** for the backend, and **SQLite** for storing configs and chat history (since no database was specified). The Playwright tests will validate the core functionality.

---

### Implementation Overview
- **Frontend**: React app with components for login, chat, config management, and code execution.
- **Backend**: Node.js/Express API to handle user auth, configs, chat history, and code execution.
- **Database**: SQLite to store users, configurations, and chat history (as a tree).
- **Testing**: Playwright tests for configuration, chat, and code execution in headed mode.
- **Assumptions**:
  - Basic user auth (username/password).
  - Chat interacts with a mock AI API (replaceable with a real one like OpenAI).
  - Code execution uses a simple sandbox (Node.js `vm` module for safety).
  - Chat history is stored as a tree (parent-child messages).

---

### Directory Structure
```
ai-chat-app/
├── client/                     # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.js
│   │   │   ├── ConfigManager.js
│   │   │   ├── CodeExecutor.js
│   │   │   └── Login.js
│   │   ├── App.js
│   │   ├── index.js
│   │   └── styles.css
│   ├── package.json
├── server/                     # Node.js backend
│   ├── src/
│   │   ├── routes/
│   │   │   ├── auth.js
│   │   │   ├── config.js
│   │   │   ├── chat.js
│   │   │   └── code.js
│   │   ├── db.js
│   │   └── server.js
│   ├── package.json
├── tests/                      # Playwright tests
│   ├── config.test.js
│   ├── chat.test.js
│   └── code-execution.test.js
├── playwright.config.js
└── README.md
```

---

### Backend Implementation (`server/`)

#### `server/package.json`
```json
{
  "name": "ai-chat-server",
  "version": "1.0.0",
  "scripts": {
    "start": "node src/server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "sqlite3": "^5.1.6",
    "jsonwebtoken": "^9.0.0",
    "cors": "^2.8.5",
    "vm2": "^3.9.19"
  }
}
```

#### `server/src/db.js`
```javascript
const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database(':memory:'); // Use file-based DB for persistence

db.serialize(() => {
  db.run(`CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)`);
  db.run(`CREATE TABLE configs (id INTEGER PRIMARY KEY, userId INTEGER, name TEXT, baseUrl TEXT, apiKey TEXT, modelId TEXT)`);
  db.run(`CREATE TABLE chats (id INTEGER PRIMARY KEY, userId INTEGER, parentId INTEGER, message TEXT, response TEXT, timestamp DATETIME)`);
});

module.exports = db;
```

#### `server/src/server.js`
```javascript
const express = require('express');
const cors = require('cors');
const authRoutes = require('./routes/auth');
const configRoutes = require('./routes/config');
const chatRoutes = require('./routes/chat');
const codeRoutes = require('./routes/code');

const app = express();
app.use(cors());
app.use(express.json());

app.use('/auth', authRoutes);
app.use('/config', configRoutes);
app.use('/chat', chatRoutes);
app.use('/code', codeRoutes);

app.listen(5000, () => console.log('Server running on http://localhost:5000'));
```

#### `server/src/routes/auth.js`
```javascript
const express = require('express');
const jwt = require('jsonwebtoken');
const db = require('../db');
const router = express.Router();

router.post('/login', (req, res) => {
  const { username, password } = req.body;
  db.get('SELECT * FROM users WHERE username = ?', [username], (err, user) => {
    if (err || !user || user.password !== password) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    const token = jwt.sign({ userId: user.id }, 'secret', { expiresIn: '1h' });
    res.json({ token });
  });
});

router.post('/register', (req, res) => {
  const { username, password } = req.body;
  db.run('INSERT INTO users (username, password) VALUES (?, ?)', [username, password], (err) => {
    if (err) return res.status(400).json({ error: 'Username exists' });
    res.json({ message: 'User created' });
  });
});

module.exports = router;
```

#### `server/src/routes/config.js`
```javascript
const express = require('express');
const jwt = require('jsonwebtoken');
const db = require('../db');
const router = express.Router();

const authenticate = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token' });
  jwt.verify(token, 'secret', (err, decoded) => {
    if (err) return res.status(401).json({ error: 'Invalid token' });
    req.userId = decoded.userId;
    next();
  });
};

router.get('/', authenticate, (req, res) => {
  db.all('SELECT * FROM configs WHERE userId = ?', [req.userId], (err, configs) => {
    if (err) return res.status(500).json({ error: 'Database error' });
    res.json(configs);
  });
});

router.post('/', authenticate, (req, res) => {
  const { name, baseUrl, apiKey, modelId } = req.body;
  db.run(
    'INSERT INTO configs (userId, name, baseUrl, apiKey, modelId) VALUES (?, ?, ?, ?, ?)',
    [req.userId, name, baseUrl, apiKey, modelId],
    (err) => {
      if (err) return res.status(500).json({ error: 'Database error' });
      res.json({ message: 'Config saved' });
    }
  );
});

module.exports = router;
```

#### `server/src/routes/chat.js`
```javascript
const express = require('express');
const db = require('../db');
const router = express.Router();

router.post('/', (req, res) => {
  const { userId, message, parentId } = req.body;
  // Mock AI response (replace with real API call)
  const response = `AI: Echoing "${message}"`;
  db.run(
    'INSERT INTO chats (userId, parentId, message, response, timestamp) VALUES (?, ?, ?, ?, ?)',
    [userId, parentId || null, message, response, new Date()],
    function (err) {
      if (err) return res.status(500).json({ error: 'Database error' });
      res.json({ id: this.lastID, message, response });
    }
  );
});

router.get('/:userId', (req, res) => {
  db.all('SELECT * FROM chats WHERE userId = ?', [req.params.userId], (err, chats) => {
    if (err) return res.status(500).json({ error: 'Database error' });
    res.json(chats);
  });
});

module.exports = router;
```

#### `server/src/routes/code.js`
```javascript
const express = require('express');
const { VM } = require('vm2');
const router = express.Router();

router.post('/run', (req, res) => {
  const { code } = req.body;
  try {
    const vm = new VM({ timeout: 1000, sandbox: {} });
    const output = vm.run(code);
    res.json({ output: String(output) });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

module.exports = router;
```

---

### Frontend Implementation (`client/`)

#### `client/package.json`
```json
{
  "name": "ai-chat-client",
  "version": "1.0.0",
  "scripts": {
    "start": "react-scripts start"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "axios": "^1.4.0"
  }
}
```

#### `client/src/App.js`
```javascript
import React, { useState } from 'react';
import Login from './components/Login';
import Chat from './components/Chat';
import ConfigManager from './components/ConfigManager';
import './styles.css';

function App() {
  const [token, setToken] = useState(null);
  const [userId, setUserId] = useState(null);

  if (!token) {
    return <Login setToken={setToken} setUserId={setUserId} />;
  }

  return (
    <div className="app">
      <ConfigManager userId={userId} />
      <Chat userId={userId} />
    </div>
  );
}

export default App;
```

#### `client/src/components/Login.js`
```javascript
import React, { useState } from 'react';
import axios from 'axios';

function Login({ setToken, setUserId }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    try {
      const res = await axios.post('http://localhost:5000/auth/login', { username, password });
      setToken(res.data.token);
      setUserId(username); // Simplified; use real userId from JWT if needed
    } catch (err) {
      alert('Login failed');
    }
  };

  const handleRegister = async () => {
    try {
      await axios.post('http://localhost:5000/auth/register', { username, password });
      alert('Registered! Please login.');
    } catch (err) {
      alert('Registration failed');
    }
  };

  return (
    <div className="login">
      <input id="username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
      <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
      <button id="login-button" onClick={handleLogin}>Login</button>
      <button onClick={handleRegister}>Register</button>
    </div>
  );
}

export default Login;
```

#### `client/src/components/ConfigManager.js`
```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ConfigManager({ userId }) {
  const [configs, setConfigs] = useState([]);
  const [name, setName] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [modelId, setModelId] = useState('');

  useEffect(() => {
    axios.get(`http://localhost:5000/config?userId=${userId}`).then((res) => setConfigs(res.data));
  }, [userId]);

  const saveConfig = async () => {
    await axios.post('http://localhost:5000/config', { userId, name, baseUrl, apiKey, modelId });
    const res = await axios.get(`http://localhost:5000/config?userId=${userId}`);
    setConfigs(res.data);
  };

  const selectConfig = (config) => {
    setBaseUrl(config.baseUrl);
    setApiKey(config.apiKey);
    setModelId(config.modelId);
  };

  return (
    <div id="config-tab">
      <h2>Configurations</h2>
      <input id="config-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Config Name" />
      <input id="base-url" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} placeholder="Base URL" />
      <input id="api-key" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="API Key" />
      <input id="model-id" value={modelId} onChange={(e) => setModelId(e.target.value)} placeholder="Model ID" />
      <button id="save-config" onClick={saveConfig}>Save Config</button>
      <ul id="config-list">
        {configs.map((config) => (
          <li key={config.id} onClick={() => selectConfig(config)}>{config.name}</li>
        ))}
      </ul>
    </div>
  );
}

export default ConfigManager;
```

#### `client/src/components/Chat.js`
```javascript
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
```

#### `client/src/components/CodeExecutor.js`
```javascript
import React, { useState } from 'react';
import axios from 'axios';

function CodeExecutor({ code }) {
  const [output, setOutput] = useState('');

  const runCode = async () => {
    try {
      const res = await axios.post('http://localhost:5000/code/run', { code });
      setOutput(res.data.output);
    } catch (err) {
      setOutput(err.response.data.error);
    }
  };

  return (
    <div>
      <pre><code>{code}</code></pre>
      <button id="run-code-button" onClick={runCode}>Run Code</button>
      <pre id="code-output">{output}</pre>
    </div>
  );
}

export default CodeExecutor;
```

#### `client/src/styles.css`
```css
.app { display: flex; }
.login, .chat, #config-tab { padding: 20px; }
#chat-history { height: 400px; overflow-y: scroll; border: 1px solid #ccc; }
#config-list { cursor: pointer; }
#config-list li:hover { background: #f0f0f0; }
```

---

### Playwright Tests (`tests/`)

#### `playwright.config.js`
```javascript
/** @type {import('@playwright/test').PlaywrightTestConfig} */
const config = {
  use: {
    headless: false, // Headed mode
    viewport: { width: 1280, height: 720 },
    actionTimeout: 10000,
    video: 'retain-on-failure',
  },
  retries: 2,
  reporter: [['list'], ['html', { outputFolder: 'playwright-report' }]],
};

module.exports = config;
```

#### `tests/config.test.js`
```javascript
const { test, expect } = require('@playwright/test');

test.describe('User Configuration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'password123');
    await page.click('#login-button');
  });

  test('should add and switch configurations', async ({ page }) => {
    await page.click('#config-tab');
    await page.fill('#config-name', 'Test Config');
    await page.fill('#base-url', 'https://api.example.com');
    await page.fill('#api-key', 'abc123');
    await page.fill('#model-id', 'model-v1');
    await page.click('#save-config');

    const configName = await page.textContent('#config-list > li');
    expect(configName).toContain('Test Config');

    await page.fill('#config-name', 'Test Config 2');
    await page.fill('#base-url', 'https://api2.example.com');
    await page.fill('#api-key', 'xyz789');
    await page.fill('#model-id', 'model-v2');
    await page.click('#save-config');

    await page.click('#config-list > li:nth-child(1)');
    const activeUrl = await page.inputValue('#base-url');
    expect(activeUrl).toBe('https://api.example.com');

    await page.click('#config-list > li:nth-child(2)');
    const activeUrl2 = await page.inputValue('#base-url');
    expect(activeUrl2).toBe('https://api2.example.com');
  });
});
```

#### `tests/chat.test.js`
```javascript
const { test, expect } = require('@playwright/test');

test.describe('Chat Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'password123');
    await page.click('#login-button');
  });

  test('should send message and receive response', async ({ page }) => {
    await page.fill('#chat-input', 'Hello, AI!');
    await page.click('#send-button');

    await page.waitForSelector('#chat-history > div:last-child');
    const response = await page.textContent('#chat-history > div:last-child');
    expect(response).toContain('AI: Echoing "Hello, AI!"');

    const chatNodes = await page.$$('#chat-history > div');
    expect(chatNodes.length).toBeGreaterThan(0);
  });
});
```

#### `tests/code-execution.test.js`
```javascript
const { test, expect } = require('@playwright/test');

test.describe('Code Execution', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'password123');
    await page.click('#login-button');
  });

  test('should execute generated code', async ({ page }) => {
    await page.fill('#chat-input', 'Generate code: console.log("Hello")');
    await page.click('#send-button');

    await page.waitForSelector('#chat-history code');
    const code = await page.textContent('#chat-history code');
    expect(code).toContain('console.log("Hello")');

    await page.click('#run-code-button');
    const output = await page.textContent('#code-output');
    expect(output).toContain('Hello');
  });
});
```

---

### Setup Instructions
1. **Backend**:
   - Navigate to `server/`.
   - Run `npm install`.
   - Run `npm start` (starts on `http://localhost:5000`).
2. **Frontend**:
   - Navigate to `client/`.
   - Run `npm install`.
   - Run `npm start` (starts on `http://localhost:3000`).
3. **Tests**:
   - Ensure backend and frontend are running.
   - Navigate to project root.
   - Run `npm install @playwright/test`.
   - Run `npx playwright test`.
   - View report in `playwright-report/`.

---

### Notes
- **Auth**: Simple JWT-based auth. Passwords are stored in plain text for simplicity (use bcrypt in production).
- **AI API**: Mocked response (`AI: Echoing...`). Replace `chat.js` POST route with a real API call (e.g., OpenAI).
- **Code Execution**: Uses `vm2` for sandboxing. Limited to JavaScript for now; extend for Python via a different sandbox.
- **Chat Tree**: Stored with `parentId` in DB but displayed linearly in UI. Add a graph UI (e.g., Cytoscape.js) for visualization.
- **Tests**: Cover login, config management, chat, and code execution. Multi-user testing requires additional setup (e.g., multiple browser contexts).
- **Security**: Add input validation, rate limiting, and proper error handling for production.
- **Scalability**: SQLite is in-memory; use a persistent DB (e.g., PostgreSQL) for production.

If you need enhancements (e.g., real AI API integration, graph-based chat UI, or more tests), let me know!