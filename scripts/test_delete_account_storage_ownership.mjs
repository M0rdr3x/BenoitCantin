#!/usr/bin/env node
// Test the actual privileged deletion path planner without calling Supabase.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { planOwnedAccountStorageDeletes } from '../supabase/functions/_shared/delete-account-storage-ownership.mjs';

const owner = '123e4567-e89b-42d3-a456-426614174000';
const victim = '123e4567-e89b-42d3-a456-426614174001';
const plan = ({ avatar = null, sources = [], applications = [] } = {}) =>
  planOwnedAccountStorageDeletes(owner, {
    'sinjira-avatars': [avatar],
    'sinjira-character-sources': sources,
    'sinjira-character-submissions': applications,
  });

test('real avatar, canonical character images and absent paths are supported', () => {
  assert.deepEqual(plan({
    avatar: `${owner}/avatar.webp`,
    sources: [`${owner}/123e4567-e89b-42d3-a456-426614174002.png`, null, ''],
    applications: [`${owner}/legacy-image.jpg`, `${owner}/legacy-image.jpg`],
  }), {
    'sinjira-avatars': [`${owner}/avatar.webp`],
    'sinjira-character-sources': [`${owner}/123e4567-e89b-42d3-a456-426614174002.png`],
    'sinjira-character-submissions': [`${owner}/legacy-image.jpg`],
  });
  assert.deepEqual(plan(), {
    'sinjira-avatars': [],
    'sinjira-character-sources': [],
    'sinjira-character-submissions': [],
  });
});

test('cross-account files are rejected in EACH bucket', () => {
  const unrelated = `${victim}/avatar.webp`;
  assert.throws(() => plan({ avatar: unrelated }), /STORAGE_PATH_OWNERSHIP_FAILED/);
  assert.throws(() => plan({ sources: [unrelated] }), /STORAGE_PATH_OWNERSHIP_FAILED/);
  assert.throws(() => plan({ applications: [unrelated] }), /STORAGE_PATH_OWNERSHIP_FAILED/);
});

test('all buckets are validated BEFORE any later deletion can run', () => {
  assert.throws(() => plan({
    avatar: `${owner}/avatar.webp`,
    sources: [`${owner}/source.webp`],
    applications: [`${victim}/victim.webp`],
  }), /STORAGE_PATH_OWNERSHIP_FAILED/);
});

test('path traversal, encoding tricks and arbitrary URLs are rejected', () => {
  const invalid = [
    `${owner}/../${victim}/avatar.webp`,
    `${owner}/./photo.webp`,
    `${owner}/folder/../../${victim}/avatar.webp`,
    `${owner}/%2e%2e/${victim}/avatar.webp`,
    `${owner}/%2f${victim}/avatar.webp`,
    `${owner}\\..\\${victim}\\avatar.webp`,
    `${owner}//photo.webp`,
    `/${owner}/avatar.webp`,
    ` ${owner}/avatar.webp`,
    `${owner}/avatar.webp `,
    `${owner}/photo.webp?download=1`,
    `${owner}/photo.webp#fragment`,
    `https://storage.invalid/object/public/sinjira-avatars/${owner}/avatar.webp`,
    `data:image/webp;base64,aGVsbG8=`,
    `${owner}/secret\u0000.webp`,
    `${owner}/${'a'.repeat(300)}.webp`,
    `${owner}/${Array(8).fill('nested').join('/')}.webp`,
  ];
  for (const value of invalid) {
    assert.throws(() => plan({ avatar: value }), /STORAGE_PATH_OWNERSHIP_FAILED/,
      'Unsafe storage path must fail closed');
  }
});

test('untrusted arrays, other bucket names and non-string paths are rejected', () => {
  for (const bad of [0, false, {}, ['path'], 42]) {
    assert.throws(() => plan({ sources: [bad] }), /STORAGE_PATH_OWNERSHIP_FAILED/);
  }
  assert.throws(() => planOwnedAccountStorageDeletes(owner, {
    'sinjira-avatars': [], 'sinjira-character-sources': [],
    'sinjira-character-submissions': [], 'other-bucket': [],
  }), /STORAGE_PATH_OWNERSHIP_FAILED/);
  assert.throws(() => planOwnedAccountStorageDeletes('fake-user', {
    'sinjira-avatars': [], 'sinjira-character-sources': [],
    'sinjira-character-submissions': [],
  }), /STORAGE_PATH_OWNERSHIP_FAILED/);
  assert.throws(() => plan({ sources: Array(2001).fill(`${owner}/ok.webp`) }),
    /STORAGE_PATH_OWNERSHIP_FAILED/);
});

test('the live Edge route plans ALL buckets before invoking privileged deletes', () => {
  const source = readFileSync(new URL('../supabase/functions/delete-player-account/index.ts',
    import.meta.url), 'utf8');
  const planner = source.indexOf('const ownedPaths=planOwnedAccountStorageDeletes(user.id,{');
  const avatars = source.indexOf("await removeStoragePaths(service,'sinjira-avatars',ownedPaths['sinjira-avatars'])");
  const sources = source.indexOf("await removeStoragePaths(service,'sinjira-character-sources',ownedPaths['sinjira-character-sources'])");
  const applications = source.indexOf("await removeStoragePaths(service,'sinjira-character-submissions',ownedPaths['sinjira-character-submissions'])");
  assert.ok(planner > 0 && avatars > planner && sources > avatars && applications > sources);
  assert.ok(source.includes('STORAGE_PATH_OWNERSHIP_FAILED'));
  assert.ok(source.includes("privacy_service_can_delete_user"));
  assert.ok(source.includes("aal.currentLevel!=='aal2'"));
  assert.doesNotMatch(source, /removeStoragePaths\(service,'sinjira-avatars',\[profileRes/);
  assert.doesNotMatch(source, /console\.error\([^)]*avatar_path/i);
});
