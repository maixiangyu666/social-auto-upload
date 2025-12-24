let _listeners = []

export function onToast(fn) {
  _listeners.push(fn)
  return () => {
    _listeners = _listeners.filter((x) => x !== fn)
  }
}

export function toast(message, type = 'info') {
  const payload = { id: crypto.randomUUID?.() ?? String(Date.now()), type, message, ts: Date.now() }
  for (const fn of _listeners) fn(payload)
  // Fallback for debugging if no UI host is mounted yet
  if (_listeners.length === 0) {
    // eslint-disable-next-line no-console
    console[type === 'error' ? 'error' : 'log']('[toast]', type, message)
  }
}

toast.success = (m) => toast(m, 'success')
toast.error = (m) => toast(m, 'error')
toast.info = (m) => toast(m, 'info')


