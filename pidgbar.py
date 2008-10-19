#!/usr/bin/env python
"""
  Pidgin Deskbar Plug-in
    Search Pidgin contacts (may be any of AIM, gTalk, MSN etc. contacts) and open
    a new chat window.

    TODO
        Handle pidgin not started exception
"""

_debug = True

import os, xml.dom.minidom
import logging
import dbus, dbus.glib, dbus.decorators
import deskbar.interfaces.Action
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import deskbar.core.Utils
import gtk, gtk.gdk, gnome.ui, gobject, gnomevfs
import time
from gettext import gettext as _

if _debug:
    import traceback
   
LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s %(levelname)-8s %(message)s',
                   filename="/tmp/pidgbar.log",
                   filemode='a')

logging.debug("test log")

HANDLERS = ["PidginBListModule"]
BUDDY_LIST_FILE = os.path.expanduser("~/.purple/blist.xml")

class Pidgin:
    def get_pidgin_service(self):
        try:
            bus = dbus.SessionBus()
            obj = bus.get_object("im.pidgin.purple.PurpleService", "/im/pidgin/purple/PurpleObject")
            pidgin = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")
            return pidgin
        except dbus.exceptions.DBusException, e:
            #self.start_pidgin()
            logging.warning("Pidgin service not started")
            return False

    def start_pidgin(self):
        #first check that pidgin exists
        deskbar.core.Utils.spawn_async(["pidgin"])
        return True

PIDGIN = Pidgin()
##pidgin = PIDGIN.get_pidgin_service()
##if(pidgin == False):
##    PIDGIN.start_pidgin()
##    import time
##    time.sleep(2)
##    pidgin = PIDGIN.get_pidgin_service()

class Buddy:
    def __init__(self, e):
        self.element = e

    def get_name(self):
        if self.element:
            return self.element.getElementsByTagName("name")[0].firstChild.data
        else:
            return None

    def get_alias(self):
        if self.element and len(self.element.getElementsByTagName("alias")) > 0:
            return self.element.getElementsByTagName("alias")[0].firstChild.data
        else:
            return ""

    def get_account(self):
        return self.element.getAttribute("account")

    def get_protocol(self):
        return self.element.getAttribute("protocol")

    def get_isonline(self):
        try:
            if(pidgin == False):
                return "no pidgin"
            
            a = pidgin.PurpleAccountsFindAny(self.account, self.protocol)
            b = pidgin.PurpleFindBuddy(a, self.name)
            return pidgin.PurpleBuddyIsOnline(b) == 1
        except(dbus.exceptions.DBusException, NameError), e:
            logging.exception("Error creating dbus interface")
            return "Pidgin service not found"

    name = property(get_name, None)
    alias = property(get_alias, None)
    account = property(get_account, None)
    protocol = property(get_protocol, None)
    is_online = property(get_isonline, None)

class PidginBListAction (deskbar.interfaces.Action):
    def __init__(self, name, buddy):
        deskbar.interfaces.Action.__init__(self, name)
        self._buddy = buddy

    def activate(self, text=None):
            pidgin = PIDGIN.get_pidgin_service()
            if(pidgin == False):
                PIDGIN.start_pidgin()
                time.sleep(1)
                pidgin = PIDGIN.get_pidgin_service()
       
            a = pidgin.PurpleAccountsFindAny(self._buddy.account, self._buddy.protocol)
            c = pidgin.PurpleConversationNew(1, a, self._name)
        #try:
        #except(dbus.exceptions.DBusException, NameError), e:
        #    logging.exception(e)

    def get_verb(self):
        if self._buddy.is_online:
            status = "Online!"
        else:
            status = "Offline"

        return _('Chat with <b>%s</b> <i>%s</i> (%s)') % (self._buddy.alias, status, self._name )

class PidginBListMatch (deskbar.interfaces.Match):
    def __init__(self, name, buddy):
        deskbar.interfaces.Match.__init__(self, name=name, icon="im-aim", category="people")
        self.buddy = buddy
        self.add_action( PidginBListAction(name, buddy) )

    def get_hash(self):
        return self.get_name()

class PidginBListModule(deskbar.interfaces.Module):
    INFOS = {"icon": deskbar.core.Utils.load_icon("im-aim"),
            "name": _("Pidgin Buddy List"),
            "description": _("Start chatting with a buddy"),
            "version" : "1.1", # Use " so the scripts can extract the version
            "categories" : { "people" : { "name" : _("Pidgin Buddies") }}}
    INSTRUCTIONS = """Dlib build of Pidgin required. Start up Pidgin prior to using this plugin."""
   
    def __init__ (self):
        deskbar.interfaces.Module.__init__ (self)

    def query(self, qstring):
        data = xml.dom.minidom.parse(BUDDY_LIST_FILE).getElementsByTagName("buddy")
        text = qstring.lower()
        results = []

        for buddy in [Buddy(x) for x in data]: # loop instances of Buddy
            if (text in buddy.name.lower() or text in buddy.alias.lower()):
                results += [PidginBListMatch(buddy.name, buddy)]

        self._emit_query_ready( qstring, results )
        return results


if __name__ == "__main__":
    import sys
    cm = PidginBListModule()
    result = cm.query("alan")
    
    print result
    if result == None:
        sys.exit(1)
