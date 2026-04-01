import test from 'node:test'
import assert from 'node:assert/strict'

import { getLatestNoticeId, hasUnreadNotices } from './notice-badge.js'

test('getLatestNoticeId returns the max notice id even when responses are unsorted', () => {
  const latestId = getLatestNoticeId([
    { id: 3, content: 'older' },
    { id: 8, content: 'newest' },
    { id: 5, content: 'middle' },
  ])

  assert.equal(latestId, 8)
})

test('hasUnreadNotices returns true when notices exist and nothing has been seen yet', () => {
  assert.equal(hasUnreadNotices([{ id: 4 }], null), true)
})

test('hasUnreadNotices returns true when a newer notice exists than the seen notice id', () => {
  assert.equal(hasUnreadNotices([{ id: 2 }, { id: 7 }], 5), true)
})

test('hasUnreadNotices returns false when the latest notice has already been seen', () => {
  assert.equal(hasUnreadNotices([{ id: 2 }, { id: 7 }], 7), false)
})
