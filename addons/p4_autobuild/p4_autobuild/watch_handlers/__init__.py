class HandlerException(Exception):
  pass

def submit(db, watch, change):
  mod = '%s.%s' % (__name__, watch.name)
  mod = __import__(mod)
  mod = mod.watch_handlers
  mod = getattr(mod, watch.name)
  fn = getattr(mod, 'submit')
  return fn(db, watch, change)
