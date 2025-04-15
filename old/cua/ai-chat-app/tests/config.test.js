const { test, expect } = require('@playwright/test');

test.describe('User Configuration', () => {
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

  test('should add and switch configurations', async ({ page }) => {
    // Wait for config tab elements to be potentially visible after login
    await page.waitForSelector('#config-tab', { state: 'visible' });

    await page.fill('#config-name', 'Test Config');
    await page.fill('#base-url', 'https://api.example.com');
    await page.fill('#api-key', 'abc123');
    await page.fill('#model-id', 'model-v1');
    await page.click('#save-config');

    // Wait for the config list to update
    await page.waitForSelector('#config-list > li:has-text("Test Config")');
    const configName = await page.textContent('#config-list > li');
    expect(configName).toContain('Test Config');

    await page.fill('#config-name', 'Test Config 2');
    await page.fill('#base-url', 'https://api2.example.com');
    await page.fill('#api-key', 'xyz789');
    await page.fill('#model-id', 'model-v2');
    await page.click('#save-config');

    // Wait for the second config item
    await page.waitForSelector('#config-list > li:nth-child(2)');

    await page.click('#config-list > li:has-text("Test Config")');
    // Wait for input value to potentially update
    await expect(page.locator('#base-url')).toHaveValue('https://api.example.com');

    await page.click('#config-list > li:has-text("Test Config 2")');
    await expect(page.locator('#base-url')).toHaveValue('https://api2.example.com');
  });
});