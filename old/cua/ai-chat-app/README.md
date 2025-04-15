# AI Chat Web App

This project implements a basic AI chat web application with multi-user support, configurable API settings, chat history saved as a tree/graph (conceptually), and code execution capability.

It uses React for the frontend, Node.js/Express for the backend, and SQLite for storage. Playwright is used for end-to-end testing.

## Project Structure

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

## Setup Instructions

1.  **Backend**:
    *   Navigate to `server/`.
    *   Run `npm install`.
    *   Run `npm start` (starts on `http://localhost:5000`).
2.  **Frontend**:
    *   Navigate to `client/`.
    *   Run `npm install`.
    *   Run `npm start` (starts on `http://localhost:3000`).
3.  **Tests**:
    *   Ensure backend and frontend are running.
    *   Navigate to project root (`ai-chat-app/`).
    *   Run `npm install @playwright/test`.
    *   Run `npx playwright test`.
    *   View report in `playwright-report/`.

## Notes

*   **Auth**: Simple JWT-based auth. Passwords are plain text (use bcrypt in production).
*   **AI API**: Mocked response. Replace `server/src/routes/chat.js` POST route with a real API call.
*   **Code Execution**: Uses `vm2` for sandboxing (Node.js only).
*   **Chat Tree**: Stored with `parentId` but displayed linearly.
*   **Database**: Uses in-memory SQLite. Switch to a file-based or production DB for persistence.