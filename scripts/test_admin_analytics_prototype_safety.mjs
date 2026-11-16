#!/usr/bin/env node
// Exercices des blocs d'agrégation RÉELS de deux fonctions Edge, avec des
// contributions inventées. Aucun accès Supabase, utilisateur ni secret.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const analytics = readFileSync(resolve(root, 'supabase/functions/admin-analytics/index.ts'), 'utf8');
const consoleSource = readFileSync(resolve(root, 'supabase/functions/admin-console/index.ts'), 'utf8');
const AsyncFunction = Object.getPrototypeOf(async function() {}).constructor;

function extract(source, startMarker, endMarker) {
  const start = source.indexOf(startMarker);
  const end = source.indexOf(endMarker, start);
  assert.ok(start >= 0 && end > start, 'Extraction du vrai code Edge impossible: ' + startMarker);
  return source.slice(start, end);
}

const realIncrement = extract(
  analytics, 'function increment(', '\nDeno.serve('
).replace('map: Record<string, number>, key: string', 'map, key');
const increment = new Function(realIncrement + '\nreturn increment;')();
const realAdminAnalytics = extract(
  analytics, 'const results: Record<string, number> = ',
  '\n  } catch (error) {'
).replaceAll(': Record<string, number>', '');
const runAnalytics = new AsyncFunction('rows', 'increment', 'privateJson', realAdminAnalytics);

const realConsoleAnalytics = extract(
  consoleSource, "if(action==='analytics'){",
  "\n    return privateJson({ok:false,error:'Action inconnue.'"
).replace('const byGame:any=', 'const byGame=').replace('Object.values(byGame) as any[]', 'Object.values(byGame)');
const runConsole = new AsyncFunction('action', 'service', 'privateJson', realConsoleAnalytics);

const keys = ['__proto__', 'constructor', 'toString', 'valueOf', 'hasOwnProperty', 'normal'];
const fakeRows = keys.map((key, index) => ({
  game_slug: key,
  metrics: {
    result: key,
    player_count: 2,
    duration_minutes: 25,
    rounds: [{ card_a: key, card_b: key }],
  },
  feedback: {
    difficulty: key,
    rating: 4,
  },
  created_at: '2026-11-16T00:00:00Z',
}));

function privateJson(data) {
  return new Response(JSON.stringify(data), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'private, no-store, max-age=0',
    },
  });
}

async function adminConsoleResult(rows) {
  const service = {
    from(table) {
      assert.equal(table, 'internal_gameplay_contributions');
      return {
        select(columns) {
          assert.ok(columns.includes('metrics'));
          return this;
        },
        order(column) {
          assert.equal(column, 'created_at');
          return this;
        },
        limit(value) {
          assert.equal(value, 10000);
          return Promise.resolve({ data: rows, error: null });
        },
      };
    },
  };
  const response = await runConsole('analytics', service, privateJson);
  assert.ok(response instanceof Response);
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('Cache-Control'), 'private, no-store, max-age=0');
  return await response.json();
}

async function adminAnalyticsResult(rows) {
  const response = await runAnalytics(rows, increment, privateJson);
  assert.ok(response instanceof Response);
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('Cache-Control'), 'private, no-store, max-age=0');
  return await response.json();
}

test('les trois index statistiques du moteur admin n’héritent d’aucun prototype', () => {
  assert.equal((analytics.match(/Record<string, number> = Object\.create\(null\)/g) || []).length, 3);
  assert.ok(!analytics.includes('const cardCounts: Record<string, number> = {};'));
  assert.ok(analytics.includes('map[normalized] = (map[normalized] || 0) + 1;'));
});

test('la carte des jeux et sous-carte de difficulté n’héritent d’aucun prototype', () => {
  assert.ok(consoleSource.includes('const byGame:any=Object.create(null);'));
  assert.ok(consoleSource.includes('difficulty:Object.create(null)};'));
  assert.ok(!consoleSource.includes('const byGame:any={};'));
  assert.ok(!consoleSource.includes('difficulty:{}};'));
});

test('admin-analytics compte les valeurs réservées comme des données, sans mutation globale', async () => {
  const payload = await adminAnalyticsResult(fakeRows);
  assert.equal(payload.ok, true);
  assert.equal(payload.analytics.total_contributions, keys.length);
  assert.equal(payload.analytics.average_player_count, 2);
  assert.equal(payload.analytics.average_duration_minutes, 25);
  assert.equal(payload.analytics.average_rating, 4);
  for (const key of keys) {
    assert.ok(Object.hasOwn(payload.analytics.results, key), 'résultat absent: ' + key);
    assert.equal(payload.analytics.results[key], 1, key);
    assert.ok(Object.hasOwn(payload.analytics.difficulty, key), 'difficulté absente: ' + key);
    assert.equal(payload.analytics.difficulty[key], 1, key);
    assert.deepEqual(
      payload.analytics.top_cards.find(row => row.card === key),
      { card: key, count: 2 },
      'carte absente: ' + key
    );
  }
  assert.equal(Object.prototype.count, undefined);
  assert.equal({}.count, undefined);
});

test('admin-console distingue tous les slugs de jeu réservés et les difficultés', async () => {
  const payload = await adminConsoleResult(fakeRows);
  assert.equal(payload.ok, true);
  const rows = payload.analytics;
  assert.equal(Object.keys(rows).length, keys.length);
  for (const key of keys) {
    assert.ok(Object.hasOwn(rows, key), 'jeu absent: ' + key);
    const game = rows[key];
    assert.equal(game.count, 1, key);
    assert.equal(game.average_players, 2, key);
    assert.equal(game.average_duration, 25, key);
    assert.equal(game.average_rating, 4, key);
    assert.ok(Object.hasOwn(game.difficulty, key), 'difficulté absente dans ' + key);
    assert.equal(game.difficulty[key], 1, key);
  }
  assert.equal(Object.prototype.count, undefined);
  assert.equal(Object.prototype.difficulty, undefined);
});

test('valeurs ordinaires et compteurs répétés restent identiques', async () => {
  const rows = [fakeRows.at(-1), fakeRows.at(-1), fakeRows.at(-1)];
  const analyticsResult = await adminAnalyticsResult(rows);
  assert.equal(analyticsResult.analytics.results.normal, 3);
  assert.equal(analyticsResult.analytics.difficulty.normal, 3);
  assert.equal(analyticsResult.analytics.top_cards[0].card, 'normal');
  assert.equal(analyticsResult.analytics.top_cards[0].count, 6);

  const consoleResult = await adminConsoleResult(rows);
  assert.equal(consoleResult.analytics.normal.count, 3);
  assert.equal(consoleResult.analytics.normal.difficulty.normal, 3);
  assert.equal(consoleResult.analytics.normal.average_players, 2);
});

test('aucun effet secondaire global après deux séries indépendantes', async () => {
  const first = await adminConsoleResult(fakeRows);
  const second = await adminConsoleResult(fakeRows);
  assert.deepEqual(first, second);
  assert.equal(({}).count, undefined);
  assert.equal(({}).difficulty, undefined);
  assert.equal(({}).normal, undefined);
});
