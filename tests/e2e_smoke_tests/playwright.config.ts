import { defineConfig, devices } from 'playwright/test';

export default defineConfig({
  testDir: './src',
  testMatch: '**/*.test.ts',
  use: {
    ...devices['iPhone 12'],
    headless: true,
  },
});
