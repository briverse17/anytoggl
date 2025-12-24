# anytoggl - TODO

## API Rate Limit Optimizations

Toggl Free plan limits: **30 requests/hour** for organization endpoints (create/update).

### Priority Improvements

- [ ] **Cache projects** - Store project list locally, refresh only when needed
- [ ] **Reduce sync frequency** - Run every 15-30 min instead of continuously
- [ ] **Diff before sync** - Only create/update entries that actually changed
- [ ] **Batch operations** - Group multiple updates where possible

### Future Considerations

- [ ] Upgrade to Toggl Starter plan (240 req/hour) if usage grows
- [ ] Add retry logic with exponential backoff for 402/429 errors
- [ ] Track quota usage via `X-Toggl-Quota-Remaining` header
