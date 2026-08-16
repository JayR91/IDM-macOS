"""Optional native macOS affordances.

The download engine remains usable without PyObjC.  On macOS, installing the
optional dependency enables a Dock badge, native notifications/chime, a menu
bar utility, and dropping URLs onto its menu-bar icon.
"""

import platform
import subprocess


class MacIntegration:
    def __init__(self, add_url_callback=None, show_callback=None, quit_callback=None):
        self.available = False
        self.status_item = None
        self._add_url = add_url_callback
        self._show = show_callback
        self._quit = quit_callback
        if platform.system() != "Darwin":
            return
        try:
            from AppKit import NSApplication, NSStatusBar, NSVariableStatusItemLength
            self.NSApplication = NSApplication
            self.NSStatusBar = NSStatusBar
            self.NSVariableStatusItemLength = NSVariableStatusItemLength
            self.available = True
        except ImportError:
            return

    def install_menu_bar(self):
        if not self.available or self.status_item:
            return
        from AppKit import NSMenu, NSMenuItem, NSView, NSPasteboardTypeURL, NSPasteboardTypeFileURL
        from Foundation import NSObject
        integration = self

        class DropView(NSView):
            def initWithFrame_(self, frame):
                self = super().initWithFrame_(frame)
                if self is not None:
                    self.registerForDraggedTypes_([NSPasteboardTypeURL, NSPasteboardTypeFileURL])
                return self

            def draggingEntered_(self, sender):
                # NSDragOperationCopy; using its numeric value avoids an SDK-version import.
                return 1

            def performDragOperation_(self, sender):
                board = sender.draggingPasteboard()
                value = board.stringForType_(NSPasteboardTypeURL) or board.stringForType_(NSPasteboardTypeFileURL)
                if value and integration._add_url:
                    integration._add_url(str(value))
                    return True
                return False

            def mouseDown_(self, event):
                if integration.status_item and integration._menu:
                    integration.status_item.popUpStatusItemMenu_(integration._menu)

            def drawRect_(self, rect):
                from AppKit import NSColor, NSFont, NSAttributedString
                NSColor.clearColor().set()
                # Keep the view recognisable even in a crowded menu bar.
                NSAttributedString.alloc().initWithString_attributes_("⇩", {"NSFont": NSFont.systemFontOfSize_(16)}).drawAtPoint_((4, 1))

        self.status_item = self.NSStatusBar.systemStatusBar().statusItemWithLength_(26)
        view = DropView.alloc().initWithFrame_(((0, 0), (26, 22)))
        self.status_item.setView_(view)
        menu = NSMenu.alloc().init()
        open_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Show IDM Clone", "showWindow:", "")
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit IDM Clone", "quitApp:", "")

        class Actions(NSObject):
            def showWindow_(self, sender):
                if integration._show:
                    integration._show()
            def quitApp_(self, sender):
                if integration._quit:
                    integration._quit()

        self._actions = Actions.alloc().init()
        open_item.setTarget_(self._actions)
        quit_item.setTarget_(self._actions)
        menu.addItem_(open_item)
        menu.addItem_(quit_item)
        self._menu = menu
        self.status_item.setMenu_(menu)

    def set_dock_badge(self, label: str):
        if self.available:
            self.NSApplication.sharedApplication().dockTile().setBadgeLabel_(label or None)

    def notify_completion(self, title: str, body: str):
        if self.available:
            try:
                from Foundation import NSUserNotification, NSUserNotificationCenter
                note = NSUserNotification.alloc().init()
                note.setTitle_(title)
                note.setInformativeText_(body)
                NSUserNotificationCenter.defaultUserNotificationCenter().deliverNotification_(note)
                return
            except Exception:
                pass
        # Works on every reasonably current macOS release, including where the
        # old NSUserNotification API is unavailable.
        escaped_title = title.replace('"', '\\"')
        escaped_body = body.replace('"', '\\"')
        subprocess.Popen(["osascript", "-e", f'display notification "{escaped_body}" with title "{escaped_title}"'])

    def play_completion_sound(self):
        if self.available:
            try:
                from AppKit import NSSound
                sound = NSSound.soundNamed_("Glass")
                if sound:
                    sound.play()
                    return
            except Exception:
                pass
        subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
