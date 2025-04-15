const { test, expect } = require('@playwright/test');

test.describe('Code Execution', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    // Need to register the user first if the DB is in-memory and resets
    try {
      await page.fill('#username', 'testuser');
      await page.fill('#password', 'password123');
      await page.click('button:has-text("Register")');
      await page.waitForTimeout(500); // Give time for registration
    } catch (e) {
      // Ignore if registration fails (user might already exist)
    }
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'password123');
    await page.click('#login-button');
    await page.waitForURL('http://localhost:3000/'); // Wait for login redirect/state change
  });

  test('should execute generated code', async ({ page }) => {
    // Wait for chat input to be ready after login
    await page.waitForSelector('#chat-input', { state: 'visible' });

    // Send a message that should trigger a code block response from the mock backend
    // The mock backend echoes the message, so we need to include ```javascript ... ```
    const codeToRun = 'console.log("Hello Execution")';
    const messageWithCode = `Please run this: \`\`\`javascript\n${codeToRun}\n\`\`\``;
    await page.fill('#chat-input', messageWithCode);
    await page.click('#send-button');

    // Wait for the code block and run button to appear in the chat history
    await page.waitForSelector('#chat-history div:last-child code', { timeout: 5000 });
    await page.waitForSelector('#chat-history div:last-child #run-code-button', { state: 'visible' });

    const codeElement = page.locator('#chat-history div:last-child code');
    await expect(codeElement).toContainText(codeToRun);

    await page.click('#chat-history div:last-child #run-code-button');

    // Wait for the output pre to appear and contain the expected text
    const outputElement = page.locator('#chat-history div:last-child #code-output');
    await expect(outputElement).toContainText('Hello Execution', { timeout: 5000 });
  });
});