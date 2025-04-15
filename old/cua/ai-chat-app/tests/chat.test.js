const { test, expect } = require('@playwright/test');

test.describe('Chat Functionality', () => {
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

  test('should send message and receive response', async ({ page }) => {
    // Wait for chat input to be ready after login
    await page.waitForSelector('#chat-input', { state: 'visible' });

    await page.fill('#chat-input', 'Hello, AI!');
    await page.click('#send-button');

    // Wait for the chat history to update with the new message/response
    await page.waitForSelector('#chat-history > div:last-child p:has-text("AI: Echoing")', { timeout: 5000 });

    const responseElement = page.locator('#chat-history > div:last-child');
    await expect(responseElement).toContainText('You: Hello, AI!');
    await expect(responseElement).toContainText('AI: Echoing "Hello, AI!"');

    const chatNodes = await page.$$('#chat-history > div');
    expect(chatNodes.length).toBeGreaterThan(0); // Check that at least one chat entry exists
  });
});