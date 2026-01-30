import { chromium } from 'playwright';

const userDataDir = 'C:/Users/black/AppData/Local/Google/Chrome/User Data';

const browser = await chromium.launchPersistentContext(userDataDir, {
  headless: false,
  channel: 'chrome',
  args: ['--profile-directory=Default']
});

console.log('Browser launched with 江口那都 profile');
console.log('Press Ctrl+C to close');

await new Promise(() => {});
