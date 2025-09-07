import { defineConfig, devices } from 'playwright/test';

export default defineConfig({
  use: {
    ...devices['iPhone 12'],
    headless: true,
  },
});
