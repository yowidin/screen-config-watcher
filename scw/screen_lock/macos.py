# noinspection PyPackageRequirements,PyUnresolvedReferences
class MacOS:
    def __init__(self, on_lock, on_unlock):
        self.on_lock = on_lock
        self.on_unlock = on_unlock

        from Foundation import NSDistributedNotificationCenter
        dnc = NSDistributedNotificationCenter.defaultCenter()
        dnc.addObserver_selector_name_object_(self, '_on_screen_locked', 'com.apple.screenIsLocked', None)
        dnc.addObserver_selector_name_object_(self, '_on_screen_unlocked', 'com.apple.screenIsUnlocked', None)

    def _on_screen_locked(self):
        self.on_lock()

    def _on_screen_unlocked(self):
        self.on_unlock()
