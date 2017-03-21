'''
Created on 2016. 10. 24.

@author: "comfact"
'''

NEXDIPY_REFRESH_SEC = 180
NEXDIPY_SUBSCRIBER_REFRESH_SEC = 60

#===============================================================================
# Exception & Error
#===============================================================================

class ExceptNexdipySession(Exception):
    def __init__(self, session):
        Exception.__init__(self, '[Error]Nexdipy:Session:%s' % session.url)
        if session.debug: print('[Error]Nexdipy:Session:%s' % session.url)

class ExceptNexdipyResponse(Exception):
    def __init__(self, session, code, text):
        Exception.__init__(self, '[Error]Nexdipy:Response:%s:%s' % (code, text))
        if session.debug: print('[Error]Nexdipy:Response:%s:%s' % (code, text))
        
class ExceptNexdipySubscriberSession(Exception):
    def __init__(self, subscriber):
        Exception.__init__(self, '[Error]Nexdipy:Subscriber:Session:wss://%s/socket%s' % (subscriber.controller.ip, subscriber.controller.cookie))
        if subscriber.controller.debug: print('[Error]Nexdipy:Subscriber:Session:wss://%s/socket%s' % (subscriber.controller.ip, subscriber.controller.cookie))

class ExceptNexdipySubscriberRegister(Exception):
    def __init__(self, subscriber, exp=None):
        Exception.__init__(self, '[Error]Nexdipy:Subscriber:Register:wss://%s/socket%s:%s' % (subscriber.controller.ip, subscriber.controller.cookie, str(exp)))
        if subscriber.controller.debug: print('[Error]Nexdipy:Subscriber:Register:wss://%s/socket%s:%s' % (subscriber.controller.ip, subscriber.controller.cookie, str(exp)))

class ExceptNexdipyProcessing(Exception):
    def __init__(self, session, msg):
        Exception.__init__(self, '[Error]Nexdipy:Processing:%s:' % msg)
        if session.debug: print('[Error]Nexdipy:Processing:%s:' % msg)

class ExceptNexdipyAttributes(Exception):
    def __init__(self, session, target, exp):
        Exception.__init__(self, '[Error]Nexdipy:Attributes:%s:%s' % (target, str(exp)))
        if session.debug: print('[Error]Nexdipy:Attributes:%s:%s' % (target, str(exp)))

class ExceptNexdipyRetriveObject(Exception):
    def __init__(self, session, target, exp):
        Exception.__init__(self, '[Error]Nexdipy:RetriveObject:%s:%s' % (target, str(exp)))
        if session.debug: print('[Error]Nexdipy:RetriveObject:%s:%s' % (target, str(exp)))

class ExceptNexdipyCreateObject(Exception):
    def __init__(self, session, target, exp):
        Exception.__init__(self, '[Error]Nexdipy:CreateObject:%s:%s' % (target, str(exp)))
        if session.debug: print('[Error]Nexdipy:CreateObject:%s:%s' % (target, str(exp)))

class ExceptNexdipyUpdateObject(Exception):
    def __init__(self, session, target, exp):
        Exception.__init__(self, '[Error]Nexdipy:UpdateObject:%s:%s' % (target, str(exp)))
        if session.debug: print('[Error]Nexdipy:UpdateObject:%s:%s' % (target, str(exp)))

class ExceptNexdipyDeleteObject(Exception):
    def __init__(self, session, target, exp):
        Exception.__init__(self, '[Error]Nexdipy:DeleteObject:%s:%s' % (target, str(exp)))
        if session.debug: print('[Error]Nexdipy:DeleteObject:%s:%s' % (target, str(exp)))

class ExceptNexdipyRelateObject(Exception):
    def __init__(self, session, target, exp):
        Exception.__init__(self, '[Error]Nexdipy:RelateObject:%s:%s' % (target, str(exp)))
        if session.debug: print('[Error]Nexdipy:RelateObject:%s:%s' % (target, str(exp)))

class ExceptNexdipyNonExistData(Exception):
    def __init__(self, session, target):
        Exception.__init__(self, '[Error]Nexdipy:NonExistData:%s' % target)
        if session.debug: print('[Error]Nexdipy:NonExistData:%s' % target)

class ExceptNexdipyNonExistCount(Exception):
    def __init__(self, session, target):
        Exception.__init__(self, '[Error]Nexdipy:NonExistCount:%s' % target)
        if session.debug: print('[Error]Nexdipy:NonExistCount:%s' % target)

class ExceptNexdipyNonExistParent(Exception):
    def __init__(self, session, target):
        Exception.__init__(self, '[Error]Nexdipy:NonExistParent:%s' % target)
        if session.debug: print('[Error]Nexdipy:NonExistParent:%s' % target)

class ExceptNexdipyNonExistHealth(Exception):
    def __init__(self, session, target):
        Exception.__init__(self, '[Error]Nexdipy:NonExistHealth:%s' % target)
        if session.debug: print('[Error]Nexdipy:NonExistHealth:%s' % target)

#===============================================================================
# Prepare Classes
#===============================================================================
PREPARE_CLASSES = {
    'topSystem' :           'nexSystemObject',
    'interfaceEntity' :     'nexInterfaceObject',
    'l1PhysIf' :            'nexPhysIfObject', 
    'l3Inst' :              'nexContextObject',
}

PREPARE_ATTRIBUTES = {
}