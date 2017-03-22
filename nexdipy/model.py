'''
Created on 2016. 10. 18.

@author: "comfact"
'''

import re
import ssl
import json
import gevent

from websocket import create_connection
from pygics import Task, RestAPI

from .static import *
from .session import Session

#######################################################################################################
#  ________  ___  ___  ________  ________  ________  ________  ___  ________  _______   ________      #
# |\   ____\|\  \|\  \|\   __  \|\   ____\|\   ____\|\   __  \|\  \|\   __  \|\  ___ \ |\   __  \     #
# \ \  \___|\ \  \\\  \ \  \|\ /\ \  \___|\ \  \___|\ \  \|\  \ \  \ \  \|\ /\ \   __/|\ \  \|\  \    #
#  \ \_____  \ \  \\\  \ \   __  \ \_____  \ \  \    \ \   _  _\ \  \ \   __  \ \  \_|/_\ \   _  _\   #
#   \|____|\  \ \  \\\  \ \  \|\  \|____|\  \ \  \____\ \  \\  \\ \  \ \  \|\  \ \  \_|\ \ \  \\  \|  #
#     ____\_\  \ \_______\ \_______\____\_\  \ \_______\ \__\\ _\\ \__\ \_______\ \_______\ \__\\ _\  #
#    |\_________\|_______|\|_______|\_________\|_______|\|__|\|__|\|__|\|_______|\|_______|\|__|\|__| #
#    \|_________|                  \|_________|                                                       #
#######################################################################################################

class SubscribeHandler:
    def subscribe(self, status, obj): pass

class Subscriber:
    
    #===========================================================================
    # Background Workers
    #===========================================================================
    class RefreshWork(Task):
        
        def __init__(self, subscriber, refresh_sec):
            Task.__init__(self, refresh_sec, refresh_sec)
            self.subscriber = subscriber
        
        def run(self):
            try: self.subscriber.__refresh__()
            except Exception as e:
                if self.subscriber.node.debug: print('[Error]Nexdipy:Subscriber:RefreshWork:%s' % str(e))
    
    class ReceiveWork(Task):
        
        def __init__(self, subscriber):
            Task.__init__(self)
            self.subscriber = subscriber
        
        def run(self):
            try: self.subscriber.__receive__()
            except Exception as e:
                if self.subscriber.node.debug: print('[Error]Nexdipy:Subscriber:ReceiveWork:%s' % str(e))
        
    #===========================================================================
    # Subscriber    
    #===========================================================================
    def __init__(self, node):
        self.node = node
        self.socket = None
        self.handlers = {}
        self.conn_status = True
        self.__connect__()
        self.receive_work = Subscriber.ReceiveWork(self).start()
        self.refresh_work = Subscriber.RefreshWork(self, NEXDIPY_SUBSCRIBER_REFRESH_SEC).start()
        
    def __connect__(self):
        if not self.conn_status: return
        if self.socket != None: self.socket.close()
        for _ in range(0, self.node.retry):
            try: self.socket = create_connection('wss://%s/socket%s' % (self.node.ip, self.node.cookie), sslopt={'cert_reqs': ssl.CERT_NONE})
            except: continue
            if self.node.debug: print('[Info]Nexdipy:Subscriber:Session:wss://%s/socket%s' % (self.node.ip, self.node.cookie))
            return
        raise Subscriber.ExceptNexdipySubscriberSession(self)
    
    def __refresh__(self):
        for subscribe_id in self.handlers:
            try: self.node.get('/api/subscriptionRefresh.json?id=%s' % subscribe_id)
            except: continue
    
    def __receive__(self):
        try:
            data = json.loads(self.socket.recv())
            subscribe_ids = data['subscriptionId']
            if not isinstance(subscribe_ids, list): subscribe_ids = [subscribe_ids]
            subscribe_data = data['imdata']
        except: self.__connect__()
        else:
            for sd in subscribe_data:
                for class_name in sd:
                    nexdipy_obj = ObjectInterface(**sd[class_name]['attributes'])
                    if class_name in PREPARE_CLASSES: nexdipy_obj.__setup__(self.node, True, class_name, PREPARE_CLASSES[class_name])
                    else: nexdipy_obj.__setup__(self.node, True, class_name)
                    for subscribe_id in subscribe_ids:
                        try: self.handlers[subscribe_id].subscribe(nexdipy_obj['status'], nexdipy_obj)
                        except Exception as e:
                            if self.node.debug: print('[Error]Nexdipy:Subscriber:Handler:%s' % str(e))
    
    def close(self):
        self.conn_status = False
        self.refresh_work.stop()
        self.receive_work.stop()
        self.socket.close()
    
    def register(self, handler):
        try: resp = self.node.session.get(self.node.url + '/api/class/%s.json?subscription=yes' % handler.class_name)
        except Exception as e: raise Subscriber.ExceptNexdipySubscriberRegister(self, e)
        if resp.status_code == 200:
            try:
                data = resp.json()
                subscription_id = data['subscriptionId']
                self.handlers[subscription_id] = handler
                return subscription_id
            except Exception as e: raise Subscriber.ExceptNexdipySubscriberRegister(self, e)
        else: raise Subscriber.ExceptNexdipySubscriberRegister(self)
        
##############################################################################################
#  ___  ________   _________  _______   ________  ________ ________  ________  _______       #
# |\  \|\   ___  \|\___   ___\\  ___ \ |\   __  \|\  _____\\   __  \|\   ____\|\  ___ \      #
# \ \  \ \  \\ \  \|___ \  \_\ \   __/|\ \  \|\  \ \  \__/\ \  \|\  \ \  \___|\ \   __/|     #
#  \ \  \ \  \\ \  \   \ \  \ \ \  \_|/_\ \   _  _\ \   __\\ \   __  \ \  \    \ \  \_|/__   #
#   \ \  \ \  \\ \  \   \ \  \ \ \  \_|\ \ \  \\  \\ \  \_| \ \  \ \  \ \  \____\ \  \_|\ \  #
#    \ \__\ \__\\ \__\   \ \__\ \ \_______\ \__\\ _\\ \__\   \ \__\ \__\ \_______\ \_______\ #
#     \|__|\|__| \|__|    \|__|  \|_______|\|__|\|__|\|__|    \|__|\|__|\|_______|\|_______| #
#                                                                                            #
##############################################################################################

#===============================================================================
# Actor
#===============================================================================
class RootInterface:
        
    def __init__(self, node, class_name):
        self.node = node
        self.class_name = class_name
        if class_name in PREPARE_CLASSES: self.prepare_class = PREPARE_CLASSES[class_name]
        else: self.prepare_class = None
    
    def keys(self):
        if self.class_name in PREPARE_ATTRIBUTES: return PREPARE_ATTRIBUTES[self.class_name]
        url = '/api/class/' + self.class_name + '.json?page=0&page-size=1'
        data = self.node.get(url)
        try: keys = sorted(data[0][self.class_name]['attributes'].keys())
        except: raise ExceptNexdipyAttributes()
        if 'childAction' in keys: keys.remove('childAction')
        if 'dn' in keys: keys.remove('dn'); keys.insert(0, 'dn')
        if 'name' in keys: keys.remove('name'); keys.insert(0, 'name')
        if 'id' in keys: keys.remove('id'); keys.insert(0, 'id')
        PREPARE_ATTRIBUTES[self.class_name] = keys
        return keys
        
    def list(self, detail=False, sort=None, page=None, **clause):
        url = '/api/node/class/' + self.class_name + '.json?'
        if not detail: url += '&rsp-prop-include=naming-only'
        if len(clause) > 0:
            url += '&query-target-filter=and('
            for key in clause: url += 'eq(%s.%s,"%s"),' % (self.class_name, key, clause[key])
            url += ')'
        if sort != None:
            url += '&order-by='
            if isinstance(sort, list):
                for s in sort: url += self.class_name + ('.%s,' % s)
            else: url += self.class_name + ('.%s' % sort)
        if page != None:
            url += '&page=%d&page-size=%d' % (page[0], page[1])
        try: data = self.node.get(url)
        except Exception as e: raise ExceptNexdipyRetriveObject(self.node, self.class_name, e)
        ret = []
        for d in data:
            for class_name in d:
                nexdipy_obj = ObjectInterface(**d[class_name]['attributes'])
                nexdipy_obj.__setup__(self.node, detail, class_name, self.prepare_class)
                ret.append(nexdipy_obj)
        return ret
    
    def count(self, **clause):
        url = '/api/node/class/' + self.class_name + '.json?'
        if len(clause) > 0:
            url += '&query-target-filter=and('
            for key in clause: url += 'eq(%s.%s,"%s"),' % (self.class_name, key, clause[key])
            url += ')'
        url += '&rsp-subtree-include=count'
        try: data = self.node.get(url)
        except Exception as e: raise ExceptNexdipyRetriveObject(self.node, self.class_name, e)
        try: return int(data[0]['moCount']['attributes']['count'])
        except: raise ExceptNexdipyNonExistCount(self.node, self.class_name)
    
    def health(self):
        url = '/api/node/class/' + self.class_name + '.json?rsp-subtree-include=health'
        try: data = self.node.get(url)
        except Exception as e: raise ExceptNexdipyRetriveObject(self.node, self.class_name, e)
        ret = []
        for d in data:
            for class_name in d:
                try: hinst = d[class_name]['children'][0]['healthInst']
                except: continue
                attrs = d[class_name]['attributes']
                obj = {'dn' : attrs['dn'], 'score' : int(hinst['attributes']['cur'])}
                ret.append(obj)
        return ret
        
    def subscribe(self, handler):
        handler.class_name = self.class_name
        if self.node.subscriber == None: self.node.subscriber = Subscriber(self.node)
        self.node.subscriber.register(handler)

class PathInterface:
    
    def __init__(self, parent, class_name, class_pkey, class_ident):
        self.parent = parent
        self.node = parent.node
        self.class_name = class_name
        self.class_pkey = class_pkey
        self.class_ident = class_ident
        if class_name in PREPARE_CLASSES: self.prepare_class = PREPARE_CLASSES[class_name]
        else: self.prepare_class = None
    
    def keys(self):
        if self.class_name in PREPARE_ATTRIBUTES: return PREPARE_ATTRIBUTES[self.class_name]
        url = '/api/class/' + self.class_name + '.json?page=0&page-size=1'
        try:
            data = self.node.get(url)
            keys = sorted(data[0][self.class_name]['attributes'].keys())
        except Exception as e: raise ExceptNexdipyAttributes(self.node, self.class_name, e)
        if 'childAction' in keys: keys.remove('childAction')
        if 'dn' in keys: keys.remove('dn'); keys.insert(0, 'dn')
        if 'name' in keys: keys.remove('name'); keys.insert(0, 'name')
        if 'id' in keys: keys.remove('id'); keys.insert(0, 'id')
        PREPARE_ATTRIBUTES[self.class_name] = keys
        return keys
    
    def __call__(self, rn, detail=False):
        dn = self.parent['dn'] + (self.class_ident % rn)
        url = '/api/node/mo/' + dn + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        try: data = self.node.get(url)
        except Exception as e: raise ExceptNexdipyRetriveObject(self.node, dn, e)
        for d in data:
            for class_name in d:
                nexdipy_obj = ObjectInterface(**d[class_name]['attributes'])
                nexdipy_obj.__setup__(self.node, detail, class_name, self.prepare_class)
                return nexdipy_obj
        raise ExceptNexdipyNonExistData(self.node, dn)

    def list(self, detail=False, sort=None, page=None, **clause):
        url = '/api/node/mo/' + self.parent['dn'] + '.json?query-target=subtree&target-subtree-class=' + self.class_name
        if not detail: url += '&rsp-prop-include=naming-only'
        if len(clause) > 0:
            url += '&query-target-filter=and('
            for key in clause: url += 'eq(%s.%s,"%s"),' % (self.class_name, key, clause[key])
            url += ')'
        if sort != None:
            url += '&order-by='
            if isinstance(sort, list):
                for s in sort: url += self.class_name + ('.%s,' % s)
            else: url += self.class_name + ('.%s' % sort)
        if page != None:
            url += '&page=%d&page-size=%d' % (page[0], page[1])
        try: data = self.node.get(url)
        except Exception as e: raise ExceptNexdipyRetriveObject(self.node, self.class_name, e)
        ret = []
        for d in data:
            for class_name in d:
                nexdipy_obj = ObjectInterface(**d[class_name]['attributes'])
                nexdipy_obj.__setup__(self.node, detail, class_name, self.prepare_class)
                ret.append(nexdipy_obj)
        return ret
    
    def count(self, **clause):
        url = '/api/node/class/' + self.class_name + '.json?query-target-filter=and(wcard(' + self.class_name + '.dn,"' + self.parent['dn'] + '/.*"),'
        if len(clause) > 0:
            for key in clause: url += 'eq(%s.%s,"%s"),' % (self.class_name, key, clause[key])
        url += ')&rsp-subtree-include=count'
        try: data = self.node.get(url)
        except Exception as e: raise ExceptNexdipyRetriveObject(self.node, self.class_name, e)
        try: return int(data[0]['moCount']['attributes']['count'])
        except: raise ExceptNexdipyNonExistCount(self.node, self.class_name)
        
    def health(self):
        url = '/api/node/class/' + self.class_name + '.json?query-target-filter=wcard(' + self.class_name + '.dn,"' + self.parent['dn'] + '/.*")&rsp-subtree-include=health'
        try: data = self.node.get(url)
        except Exception as e: raise ExceptNexdipyRetriveObject(self.node, self.class_name, e)
        ret = []
        for d in data:
            for class_name in d:
                try: hinst = d[class_name]['children'][0]['healthInst']
                except: continue
                attrs = d[class_name]['attributes']
                obj = {'dn' : attrs['dn'], 'score' : int(hinst['attributes']['cur'])}
                ret.append(obj)
        return ret
    
    def subscribe(self, handler):
        handler.class_name = self.class_name
        if self.node.subscriber == None: self.node.subscriber = Subscriber(self.node)
        self.node.subscriber.register(handler)
        
    def create(self, **attributes):
        if self.prepare_class == None: raise ExceptNexdipyCreateObject(self.node, self.class_name, ExceptNexdipyProcessing(self.node, 'Uncompleted Identifier'))
        nexdipy_obj = ObjectInterface(**attributes)
        try: ret = self.node.post('/api/node/mo/' + self.parent['dn'] + '.json', nexdipy_obj.toJson())
        except Exception as e: raise ExceptNexdipyCreateObject(self.node, self.class_name, e)
        if ret:
            nexdipy_obj['dn'] = self.parent['dn'] + (self.class_ident % attributes[self.class_pkey])
            nexdipy_obj.__setup__(self.node, False, self.class_name, self.prepare_class)
            return nexdipy_obj
        raise ExceptNexdipyCreateObject(self.node, self.class_name, ExceptNexdipyProcessing(self.node, 'Creation Failed'))

class PodRootInterface:
     
    def __init__(self, pod, class_name):
        self.pod = pod
        self.class_name = class_name
         
    def list(self, detail=False, sort=None, page=None, **clause):
        ret = {}; fetchs = []
        def fetch(pod, node_name, class_name, detail, sort, page, clause, ret): ret[node_name] = pod[node_name].Class(class_name).list(detail, sort, page, **clause)
        for node_name in self.pod: fetchs.append(gevent.spawn(fetch, self.pod, node_name, self.class_name, detail, sort, page, clause, ret))
        gevent.joinall(fetchs)
        return ret
     
    def count(self, **clause):
        ret = {}; fetchs = []
        def fetch(pod, node_name, class_name, clause, ret): ret[node_name] = pod[node_name].Class(class_name).count(**clause)
        for node_name in self.pod: fetchs.append(gevent.spawn(fetch, self.pod, node_name, self.class_name, clause, ret))
        gevent.joinall(fetchs)
        return ret
    
    def health(self):
        ret = {}; fetchs = []
        def fetch(pod, node_name, class_name, ret): ret[node_name] = pod[node_name].Class(class_name).health()
        for node_name in self.pod: fetchs.append(gevent.spawn(fetch, self.pod, node_name, self.class_name, ret))
        gevent.joinall(fetchs)
        return ret

class PodPathInterface:
         
    def __init__(self, pod, actor_name):
        self.pod = pod
        self.actor_name = actor_name
     
    def list(self, detail=False, sort=None, page=None, **clause):
        ret = {}; fetchs = []
        def fetch(pod, node_name, actor_name, detail, sort, page, clause, ret): ret[node_name] = pod[node_name].__getattribute__(actor_name).list(detail, sort, page, **clause) 
        for node_name in self.pod: fetchs.append(gevent.spawn(fetch, self.pod, node_name, self.actor_name, detail, sort, page, clause, ret))
        gevent.joinall(fetchs)
        return ret
    
    def count(self, **clause):
        ret = {}; fetchs = []
        def fetch(pod, node_name, actor_name, clause, ret): ret[node_name] = pod[node_name].__getattribute__(actor_name).count(**clause)
        for node_name in self.pod: fetchs.append(gevent.spawn(fetch, self.pod, node_name, self.actor_name, clause, ret))
        gevent.joinall(fetchs)
        return ret
     
    def health(self):
        ret = {}; fetchs = []
        def fetch(pod, node_name, actor_name, ret): ret[node_name] = pod[node_name].__getattribute__(actor_name).health() 
        for node_name in self.pod: fetchs.append(gevent.spawn(fetch, self.pod, node_name, self.actor_name, ret))
        gevent.joinall(fetchs)
        return ret

class ObjectInterface(dict):
    
    def __init__(self, **attributes):
        dict.__init__(self, **attributes)
        self._object_delta = None
        
    def __setup__(self, node, detail, class_name, obj_name=None):
        self.node = node
        self.is_detail = detail
        self.class_name = class_name
        if obj_name != None:
            self.__class__ = globals()[obj_name]
            self.__patch__()
    
    def __patch__(self):
        pass
    
    def __setitem__(self, key, val):
        if self._object_delta == None: self._object_delta = {}
        self._object_delta[key] = val
        return dict.__setitem__(self, key, val)
    
    def toJson(self):
        data = {}
        data[self.class_name] = {'attributes' : self}
        return json.dumps(data)
    
    def keys(self):
        if self.class_name in PREPARE_ATTRIBUTES: return PREPARE_ATTRIBUTES[self.class_name]
        url = '/api/class/' + self.class_name + '.json?page=0&page-size=1'
        try:
            data = self.node.get(url)
            keys = sorted(data[0][self.class_name]['attributes'].keys())
        except Exception as e: raise ExceptNexdipyAttributes(self.node, self.class_name, e)
        if 'childAction' in keys: keys.remove('childAction')
        if 'dn' in keys: keys.remove('dn'); keys.insert(0, 'dn')
        if 'name' in keys: keys.remove('name'); keys.insert(0, 'name')
        if 'id' in keys: keys.remove('id'); keys.insert(0, 'id')
        PREPARE_ATTRIBUTES[self.class_name] = keys
        return keys
    
    def dn(self):
        return self['dn']
    
    def rn(self):
        dn = self['dn']
        ret = re.match('(?P<path>.*)/(?P<key>\w+)-(?P<rn>\[?[\W\w]+\]?)$', dn)
        if ret: return ret.group('path'), ret.group('key'), ret.group('rn')
        ret = re.match('^(?P<rn>\w+)$', dn)
        if ret: return None, None, ret.group('rn')
        return None, None, None
    
    def path(self):
        return re.sub('/\w+-', '/', self['dn'])
    
    def detail(self):
        if not self.is_detail:
            url = '/api/node/mo/' + self['dn'] + '.json'
            try: data = self.node.get(url)
            except Exception as e: raise ExceptNexdipyRetriveObject(self.node, self['dn'], e)
            for d in data:
                for class_name in d:
                    attrs = d[class_name]['attributes']
                    for key in attrs: self[key] = attrs[key]
            self.is_detail = True
        return self
    
    def refresh(self):
        url = '/api/node/mo/' + self['dn'] + '.json'
        try: data = self.node.get(url)
        except Exception as e: raise ExceptNexdipyRetriveObject(self.node, self['dn'], e)
        for d in data:
            for class_name in d:
                attrs = d[class_name]['attributes']
                for key in attrs: self[key] = attrs[key]
        self.is_detail = True
        self.__patch__()
        return self

    def parent(self, detail=False):
        try: parent_dn = self['dn'].split(re.match('[\W\w]+(?P<rn>/\w+-\[?[\W\w]+]?)$', self['dn']).group('rn'))[0]
        except: raise ExceptNexdipyNonExistParent(self.node, self['dn'])
        url = '/api/node/mo/' + parent_dn + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        try: data = self.node.get(url)
        except Exception as e: raise ExceptNexdipyRetriveObject(self.node, parent_dn, e)
        for d in data:
            for class_name in d:
                nexdipy_obj = ObjectInterface(**d[class_name]['attributes'])
                if class_name in PREPARE_CLASSES: nexdipy_obj.__setup__(self.node, detail, class_name, PREPARE_CLASSES[class_name])
                else: nexdipy_obj.__setup__(self.node, detail, class_name)
                return nexdipy_obj
        raise ExceptNexdipyNonExistData(self.node, parent_dn)

    def children(self, detail=False, sort=None, page=None, **clause):
        url = '/api/node/mo/' + self['dn'] + '.json?query-target=children'
        if not detail: url += '&rsp-prop-include=naming-only'
        if len(clause) > 0:
            url += '&query-target-filter=and('
            for key in clause: url += 'eq(%s.%s,"%s"),' % (self.class_name, key, clause[key])
            url += ')'
        if sort != None:
            url += '&order-by='
            if isinstance(sort, list):
                for s in sort: url += self.class_name + ('.%s,' % s)
            else: url += self.class_name + ('.%s' % sort)
        if page != None:
            url += '&page=%d&page-size=%d' % (page[0], page[1])
        try: data = self.node.get(url)
        except Exception as e: raise ExceptNexdipyRetriveObject(self.node, self['dn'] + '/children', e)
        ret = []
        for d in data:
            for class_name in d:
                nexdipy_obj = ObjectInterface(**d[class_name]['attributes'])
                if class_name in PREPARE_CLASSES: nexdipy_obj.__setup__(self.node, detail, class_name, PREPARE_CLASSES[class_name])
                else: nexdipy_obj.__setup__(self.node, detail, class_name)
                ret.append(nexdipy_obj)
        return ret
    
    def Class(self, class_name, class_pkey=None, class_ident=None):
        return PathInterface(self, class_name, class_pkey, class_ident)
    
    def update(self):
        self._object_delta['dn'] = self['dn']
        try: ret = self.node.post('/api/node/mo/' + self['dn'] + '.json', data=json.dumps({self.class_name : {'attributes' : self._object_delta}}))
        except Exception as e: raise ExceptNexdipyUpdateObject(self.node, self['dn'], e)
        if not ret: raise ExceptNexdipyUpdateObject(self.node, self['dn'], ExceptNexdipyProcessing(self.node, 'Updating Failed')) 
        return True
    
    def delete(self):
        try: ret = self.node.delete('/api/node/mo/' + self['dn'] + '.json')
        except Exception as e: raise ExceptNexdipyDeleteObject(self.node, self['dn'], e)
        if not ret: raise ExceptNexdipyDeleteObject(self.node, self['dn'], ExceptNexdipyProcessing(self.node, 'Deleting Failed'))
        return True
    
    def health(self):
        url = '/api/node/mo/' + self['dn'] + '.json?rsp-subtree-include=health'
        try: data = self.node.get(url)
        except Exception as e: raise ExceptNexdipyRetriveObject(self.node, self['dn'], e)
        for d in data:
            for class_name in d:
                try: hinst = d[class_name]['children'][0]['healthInst']
                except: continue
                return {'dn' : self['dn'], 'score' : int(hinst['attributes']['cur'])}
        raise ExceptNexdipyNonExistHealth(self.node, self['dn'])

##########################################################
#  ________  ________ _________  ________  ________      #
# |\   __  \|\   ____\\___   ___\\   __  \|\   __  \     #
# \ \  \|\  \ \  \___\|___ \  \_\ \  \|\  \ \  \|\  \    #
#  \ \   __  \ \  \       \ \  \ \ \  \\\  \ \   _  _\   #
#   \ \  \ \  \ \  \____   \ \  \ \ \  \\\  \ \  \\  \|  #
#    \ \__\ \__\ \_______\  \ \__\ \ \_______\ \__\\ _\  #
#     \|__|\|__|\|_______|   \|__|  \|_______|\|__|\|__| #
#                                                        #
##########################################################

class nexPhysIfActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'l1PhysIf', 'id', '/phys-[%s]')

class nexAggrIfActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'pcAttrIf', 'id', '/aggr-[%s]')
    
class nexContextActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'l3Inst', 'name', '/inst-%s')

###############################################################
#  _____ ______   ________  ________  _______   ___           #
# |\   _ \  _   \|\   __  \|\   ___ \|\  ___ \ |\  \          #
# \ \  \\\__\ \  \ \  \|\  \ \  \_|\ \ \   __/|\ \  \         #
#  \ \  \\|__| \  \ \  \\\  \ \  \ \\ \ \  \_|/_\ \  \        #
#   \ \  \    \ \  \ \  \\\  \ \  \_\\ \ \  \_|\ \ \  \____   #
#    \ \__\    \ \__\ \_______\ \_______\ \_______\ \_______\ #
#     \|__|     \|__|\|_______|\|_______|\|_______|\|_______| #
#                                                             #
###############################################################

class nexSystemObject(ObjectInterface):
    
    def __patch__(self):
        self.Interface = self.node('sys/intf', detail=True)
        self.Context = nexContextActor(self)
        
class nexInterfaceObject(ObjectInterface):
    
    def __patch__(self):
        self.PhysIf = nexPhysIfActor(self)

class nexPhysIfObject(ObjectInterface): pass

class nexAggrIfObject(ObjectInterface): pass

class nexContextObject(ObjectInterface): pass
        
#################################################
#  ________   ________  ________  _______       #
# |\   ___  \|\   __  \|\   ___ \|\  ___ \      #
# \ \  \\ \  \ \  \|\  \ \  \_|\ \ \   __/|     #
#  \ \  \\ \  \ \  \\\  \ \  \ \\ \ \  \_|/__   #
#   \ \  \\ \  \ \  \\\  \ \  \_\\ \ \  \_|\ \  #
#    \ \__\\ \__\ \_______\ \_______\ \_______\ #
#     \|__| \|__|\|_______|\|_______|\|_______| #
#                                               #
#################################################

class Node(Session, ObjectInterface):
    
    class CLI:
        
        def __init__(self, node):
            self.node = node
        
        def __console_line_interface__(self, cli_type, *cmd):
            headers = {'content-type':'application/json'}
            data = {'ins_api':{'version':'1.0','type':cli_type,'chunk':'0','sid':'1','input':' ;'.join(cmd),'output_format':'json'}}
            auth = (self.node.user, self.node.pwd)
            cmd_len = len(cmd)
            for _ in range(0, self.node.retry):
                resp = self.node.session.post(self.node.url + '/ins', data=json.dumps(data), headers=headers, auth=auth)
                if resp.status_code == 200:
                    results = resp.json()['ins_api']['outputs']['output']
                    if cmd_len > 1:
                        if cli_type != 'cli_conf': ret = [None for _ in cmd]
                        else: ret = [False for _ in cmd]
                        if isinstance(results, list):
                            for i in range(0, len(results)):
                                result = results[i]
                                if result['code'] == '200':
                                    if cli_type != 'cli_conf': ret[i] = result['body']
                                    else: ret[i] = True
                                else:
                                    try: err = result['clierror']
                                    except:
                                        try: err = result['basherror']
                                        except: err = None
                                    raise ExceptNexdipyCLI(self.node, result['msg'], err)
                        return ret
                    else:
                        if results['code'] == '200' :
                            if cli_type != 'cli_conf': return results['body']
                            else: return True
                        else:
                            try: err = results['clierror']
                            except:
                                try: err = results['basherror']
                                except: err = None
                            raise ExceptNexdipyCLI(self.node, results['msg'], err)
                        if cli_type != 'cli_conf': return None
                        else: return False
                elif resp.status_code == 403: self.refresh()
                else: raise ExceptNexdipyResponse(self, resp.status_code, ' ;'.join(cmd))
            raise ExceptNexdipySession(self)
        
        def User(self, *cmd):
            return self.__console_line_interface__('cli_show_ascii', *cmd)
        
        def Json(self, *cmd):
            return self.__console_line_interface__('cli_show', *cmd)
        
        def Conf(self, *cmd):
            return self.__console_line_interface__('cli_conf', *cmd)
        
        def Bash(self, *cmd):
            ret = self.__console_line_interface__('bash', ' ; echo "__NEXDIPY_LF__" ;'.join(cmd))
            return ret.split('__NEXDIPY_LF__\n')
    
    def __init__(self, ip, user, pwd, refresh_sec=NEXDIPY_REFRESH_SEC, **kargs):
        Session.__init__(self,
                         ip=ip,
                         user=user,
                         pwd=pwd,
                         refresh_sec=refresh_sec,
                         **kargs)
        ObjectInterface.__init__(self,
                                 ip=ip,
                                 user=user,
                                 pwd=pwd,
                                 refresh_sec=refresh_sec,
                                 **kargs)
        
        self.class_name = 'Node'
        self.subscriber = None
        
        self.System = self('sys', detail=True)
        self.PhysIf = RootInterface(self, 'l1PhysIf')
        self.AggrIf = RootInterface(self, 'pcAggrIf')
        self.Context = RootInterface(self, 'l3Inst')
        
        self.CLI = Node.CLI(self)
        
        self['name'] = self.System['name']
        
    def close(self):
        if self.subscriber != None: self.subscriber.close()
        Session.close(self)
                
    def detail(self):
        return self
    
    def refresh(self):
        self.System.refresh()
        return self
    
    def health(self):
        return self.System.health()['score']

    def Class(self, class_name):
        return RootInterface(self, class_name)
    
    def __call__(self, dn, detail=False):
        url = '/api/node/mo/' + dn + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        try: data = self.get(url)
        except Exception as e: raise ExceptNexdipyRetriveObject(self, dn, e)
        for d in data:
            for class_name in d:
                nexdipy_obj = ObjectInterface(**d[class_name]['attributes'])
                if class_name in PREPARE_CLASSES: nexdipy_obj.__setup__(self, detail, class_name, PREPARE_CLASSES[class_name])
                else: nexdipy_obj.__setup__(self, detail, class_name)
                return nexdipy_obj
        raise ExceptNexdipyNonExistData(self, dn)

######################################
#  ________  ________  ________      #
# |\   __  \|\   __  \|\   ___ \     #
# \ \  \|\  \ \  \|\  \ \  \_|\ \    #
#  \ \   ____\ \  \\\  \ \  \ \\ \   #
#   \ \  \___|\ \  \\\  \ \  \_\\ \  #
#    \ \__\    \ \_______\ \_______\ #
#     \|__|     \|_______|\|_______| #
#                                    #
######################################

class Pod(dict):
     
    def __init__(self,
                 conns=RestAPI.DEFAULT_CONN_SIZE,
                 conn_max=RestAPI.DEFAULT_CONN_MAX,
                 retry=RestAPI.DEFAULT_CONN_RETRY,
                 refresh_sec=NEXDIPY_REFRESH_SEC,
                 debug=False):
        dict.__init__(self)
        self.conns = conns
        self.conn_max = conn_max
        self.retry = retry
        self.refresh_sec = refresh_sec
        self.debug = debug
        self.node_ip_names = {}
        
        self.System = PodRootInterface(self, 'topSystem')
        self.PhysIf = PodPathInterface(self, 'PhysIf')
        self.AggrIf = PodPathInterface(self, 'AggrIf')
        self.Context = PodPathInterface(self, 'Context')
        
    def Class(self, class_name):
        return PodRootInterface(self, class_name)
     
    def detail(self):
        return self
    
    def refresh(self):
        return self
     
    def health(self):
        ret = {}; fetchs = []
        def fetch(pod, node_name, ret): ret[node_name] = pod[node_name].health() 
        for node_name in self: fetchs.append(gevent.spawn(fetch, self, node_name, ret))
        gevent.joinall(fetchs)
        return ret
         
    def addNode(self, ip, user, pwd):
        if ip in self.node_ip_names:
            if self.debug: print('[Error]Nxosdipy:Pod:AddNode:Already Exist Node %s' % ip)
            return None
        opts = {'ip' : ip,
                'user' : user,
                'pwd' : pwd,
                'conns' : self.conns,
                'conn_max' : self.conn_max,
                'retry' : self.retry,
                'refresh_sec' : self.refresh_sec,
                'debug' : self.debug}
        try: node = Node(**opts)
        except Exception as e:
            if self.debug: print('[Error]Nxosdipy:Pod:AddNode:%s' % str(e))
            return None
        self[node['name']] = node
        self.node_ip_names[ip] = node['name']
        return node
     
    def delNode(self, node_name):
        if node_name not in self: return False
        self[node_name].close()
        self.pop(node_name)
        ip_names = None
        for ip, name in self.node_ip_names.items():
            if name == node_name:
                ip_names = ip
                break
        if ip_names: self.node_ip_names.pop(ip_names)
        return True
     
    def close(self):
        node_names = self.keys()
        for node_name in node_names: self.delNode(node_name)

#####################################################################################
#  _____ ______   ___  ___  ___   _________  ___  ________  ________  ________      #
# |\   _ \  _   \|\  \|\  \|\  \ |\___   ___\\  \|\   __  \|\   __  \|\   ___ \     #
# \ \  \\\__\ \  \ \  \\\  \ \  \\|___ \  \_\ \  \ \  \|\  \ \  \|\  \ \  \_|\ \    #
#  \ \  \\|__| \  \ \  \\\  \ \  \    \ \  \ \ \  \ \   ____\ \  \\\  \ \  \ \\ \   #
#   \ \  \    \ \  \ \  \\\  \ \  \____\ \  \ \ \  \ \  \___|\ \  \\\  \ \  \_\\ \  #
#    \ \__\    \ \__\ \_______\ \_______\ \__\ \ \__\ \__\    \ \_______\ \_______\ #
#     \|__|     \|__|\|_______|\|_______|\|__|  \|__|\|__|     \|_______|\|_______| #
#                                                                                   #
#####################################################################################

class MultiPod(dict):
     
    def __init__(self,
                 conns=RestAPI.DEFAULT_CONN_SIZE,
                 conn_max=RestAPI.DEFAULT_CONN_MAX,
                 retry=RestAPI.DEFAULT_CONN_RETRY,
                 refresh_sec=NEXDIPY_REFRESH_SEC,
                 debug=False):
        dict.__init__(self)
        self.conns = conns
        self.conn_max = conn_max
        self.retry = retry
        self.refresh_sec = refresh_sec
        self.debug = debug
        
        self.System = PodPathInterface(self, 'System')
        self.PhysIf = PodPathInterface(self, 'PhysIf')
        self.AggrIf = PodPathInterface(self, 'AggrIf')
        self.Context = PodPathInterface(self, 'Context')
        
    def Class(self, class_name):
        return PodRootInterface(self, class_name)
     
    def detail(self):
        return self
    
    def refresh(self):
        return self
     
    def health(self):
        ret = {}; fetchs = []
        def fetch(multi_pod, pod_name, ret): ret[pod_name] = multi_pod[pod_name].health() 
        for pod_name in self: fetchs.append(gevent.spawn(fetch, self, pod_name, ret))
        gevent.joinall(fetchs)
        return ret
         
    def addPod(self, pod_name):
        if pod_name in self:
            if self.debug: print('[Error]Nxosdipy:MultiPod:AddPod:Already Exist Pod %s' % pod_name)
            return None
        opts = {'conns' : self.conns,
                'conn_max' : self.conn_max,
                'retry' : self.retry,
                'refresh_sec' : self.refresh_sec,
                'debug' : self.debug}
        try: pod = Pod(**opts)
        except Exception as e:
            if self.debug: print('[Error]Nxosdipy:MultiPod:AddPod:%s' % str(e))
            return None
        self[pod_name] = pod
        return pod
     
    def delPod(self, pod_name):
        if pod_name not in self: return False
        self[pod_name].close()
        self.pop(pod_name)
        return True
     
    def close(self):
        pod_names = self.keys()
        for pod_name in pod_names: self.delPod(pod_name)
