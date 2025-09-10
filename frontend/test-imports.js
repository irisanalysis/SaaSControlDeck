// Test file to verify module resolution
console.log('Testing module resolution...');

try {
  console.log('Testing tabs import...');
  const tabs = require('./src/components/ui/tabs.tsx');
  console.log('✅ Tabs imported successfully:', Object.keys(tabs));
} catch (e) {
  console.log('❌ Tabs import failed:', e.message);
}

try {
  console.log('Testing profile-card import...');
  const profileCard = require('./src/components/dashboard/profile-card.tsx');
  console.log('✅ ProfileCard imported successfully:', Object.keys(profileCard));
} catch (e) {
  console.log('❌ ProfileCard import failed:', e.message);
}

try {
  console.log('Testing utils import...');
  const utils = require('./src/lib/utils.ts');
  console.log('✅ Utils imported successfully:', Object.keys(utils));
} catch (e) {
  console.log('❌ Utils import failed:', e.message);
}