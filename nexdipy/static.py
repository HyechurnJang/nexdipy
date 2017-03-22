'''
Created on 2016. 10. 24.

@author: "comfact"
'''

#===============================================================================
# Default Settings
#===============================================================================
NEXDIPY_REFRESH_SEC = 180
NEXDIPY_SUBSCRIBER_REFRESH_SEC = 60

#===============================================================================
# Prepare Classes
#===============================================================================
PREPARE_CLASSES = {
    'topSystem' :           'nexSystemObject',
    'interfaceEntity' :     'nexInterfaceObject',
    'l1PhysIf' :            'nexPhysIfObject',
    'pcAttrIf' :            'nexAggrIfObject',
    'l3Inst' :              'nexContextObject',
}

PREPARE_ATTRIBUTES = {
}

#===============================================================================
# Exception & Error
#===============================================================================

class ExceptNexdipyAbstract(Exception):
    def __init__(self, session, msg):
        Exception.__init__(self, msg)
        if session.debug: print msg

class ExceptNexdipySession(ExceptNexdipyAbstract):
    def __init__(self, session):
        ExceptNexdipyAbstract.__init__(self, session, '[Error]Nexdipy:Session:%s' % session.url)

class ExceptNexdipyResponse(ExceptNexdipyAbstract):
    def __init__(self, session, code, text):
        ExceptNexdipyAbstract.__init__(self, session, '[Error]Nexdipy:Response:%s:%s' % (code, text))

class ExceptNexdipyCLI(ExceptNexdipyAbstract):
    def __init__(self, session, msg, err):
        ExceptNexdipyAbstract.__init__(self, session, '[Error]Nexdipy:CLI:%s:%s' % (msg, err))
        
class ExceptNexdipySubscriberSession(ExceptNexdipyAbstract):
    def __init__(self, subscriber):
        ExceptNexdipyAbstract.__init__(self, subscriber.node, '[Error]Nexdipy:Subscriber:Session:wss://%s/socket%s' % (subscriber.node.ip, subscriber.node.cookie))

class ExceptNexdipySubscriberRegister(ExceptNexdipyAbstract):
    def __init__(self, subscriber, exp=None):
        ExceptNexdipyAbstract.__init__(self, subscriber.node, '[Error]Nexdipy:Subscriber:Register:wss://%s/socket%s:%s' % (subscriber.node.ip, subscriber.node.cookie, str(exp)))

class ExceptNexdipyProcessing(ExceptNexdipyAbstract):
    def __init__(self, session, msg):
        ExceptNexdipyAbstract.__init__(self, session, '[Error]Nexdipy:Processing:%s:' % msg)

class ExceptNexdipyAttributes(ExceptNexdipyAbstract):
    def __init__(self, session, target, exp):
        ExceptNexdipyAbstract.__init__(self, session, '[Error]Nexdipy:Attributes:%s:%s' % (target, str(exp)))

class ExceptNexdipyRetriveObject(ExceptNexdipyAbstract):
    def __init__(self, session, target, exp):
        ExceptNexdipyAbstract.__init__(self, session, '[Error]Nexdipy:RetriveObject:%s:%s' % (target, str(exp)))

class ExceptNexdipyCreateObject(ExceptNexdipyAbstract):
    def __init__(self, session, target, exp):
        ExceptNexdipyAbstract.__init__(self, session, '[Error]Nexdipy:CreateObject:%s:%s' % (target, str(exp)))

class ExceptNexdipyUpdateObject(ExceptNexdipyAbstract):
    def __init__(self, session, target, exp):
        ExceptNexdipyAbstract.__init__(self, session, '[Error]Nexdipy:UpdateObject:%s:%s' % (target, str(exp)))

class ExceptNexdipyDeleteObject(ExceptNexdipyAbstract):
    def __init__(self, session, target, exp):
        ExceptNexdipyAbstract.__init__(self, session, '[Error]Nexdipy:DeleteObject:%s:%s' % (target, str(exp)))

class ExceptNexdipyRelateObject(ExceptNexdipyAbstract):
    def __init__(self, session, target, exp):
        ExceptNexdipyAbstract.__init__(self, session, '[Error]Nexdipy:RelateObject:%s:%s' % (target, str(exp)))

class ExceptNexdipyNonExistData(ExceptNexdipyAbstract):
    def __init__(self, session, target):
        ExceptNexdipyAbstract.__init__(self, session, '[Error]Nexdipy:NonExistData:%s' % target)

class ExceptNexdipyNonExistCount(ExceptNexdipyAbstract):
    def __init__(self, session, target):
        ExceptNexdipyAbstract.__init__(self, session, '[Error]Nexdipy:NonExistCount:%s' % target)

class ExceptNexdipyNonExistParent(ExceptNexdipyAbstract):
    def __init__(self, session, target):
        ExceptNexdipyAbstract.__init__(self, session, '[Error]Nexdipy:NonExistParent:%s' % target)

class ExceptNexdipyNonExistHealth(ExceptNexdipyAbstract):
    def __init__(self, session, target):
        ExceptNexdipyAbstract.__init__(self, session, '[Error]Nexdipy:NonExistHealth:%s' % target)
