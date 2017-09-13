#!/usr/bin/env python
# encoding: utf-8

from collections import namedtuple
from .resources import Resource
from tbone.db.models import post_save


Route = namedtuple('Route', 'path, handler, methods, name')


class Router(object):
    ''' Creates a url list for a group of resources. '''
    def __init__(self, name):
        self.name = name
        self._registry = {}

    def register(self, resource, endpoint):
        '''
        This methods registers a resource with the router and conect all receivers to their respective signals'''
        if not issubclass(resource, Resource):
            raise ValueError('Not and instance of ``Resource`` subclass')

        self._registry[endpoint] = resource
        for item in dir(resource):
            attr = getattr(resource, item)
            if hasattr(attr, '_signal_receiver_'):
                attr._signal_receiver_.connect(attr, sender=resource._meta.object_class)
        # if resource._meta.object_class is not None:
            # post_save.connect(resource.post_save, sender=resource._meta.object_class)

    def unregister(self, endpoint):
        if endpoint in self._registry:
            resource = self._registry[endpoint]
            post_save.disconnect(resource.post_save, sender=resource._meta.object_class)
            del(self._registry[endpoint])

    def endpoints(self):
        return list(self._registry)

    def urls(self):
        '''
        Iterate through all resources registered with this router
        and create a list endpoint and a detail endpoint for each one.
        Uses the router name as prefix and endpoint name of the resource when registered, to assemble the url pattern.
        Uses the constructor-passed url method or class for generating urls
        '''
        url_patterns = []
        for endpoint, resource_class in self._registry.items():
            setattr(resource_class, 'api_name', self.name)
            setattr(resource_class, 'resource_name', endpoint)
            # append any nested resources the resource may have
            url_patterns.extend(resource_class.nested_routes('/%s/%s/' % (self.name, endpoint)))
            # append resource as list
            url_patterns.append(Route(
                path='/%s/%s/' % (self.name, endpoint),
                handler=resource_class.as_list(),
                methods=resource_class.route_methods(),
                name='{}_{}_list'.format(self.name, endpoint).replace('/', '_')
            ))
            # append resource as detail
            url_patterns.append(Route(
                path='/%s/%s/{pk}/' % (self.name, endpoint),
                handler=resource_class.as_detail(),
                methods=resource_class.route_methods(),
                name='{}_{}_detail'.format(self.name, endpoint).replace('/', '_')
            ))
        return url_patterns

    def urls2(self):
        '''
        Iterate through all resources registered with this router
        and create a list endpoint and a detail endpoint for each one.
        Uses the router name as prefix and endpoint name of the resource when registered, to assemble the url pattern.
        Uses the constructor-passed url method or class for generating urls
        '''
        url_patterns = []
        for endpoint, resource_class in self._registry.items():
            setattr(resource_class, 'api_name', self.name)
            setattr(resource_class, 'resource_name', endpoint)
            # append any nested handlers the resource may have
            url_patterns.extend(resource_class.nested_routes('/(?P<api_name>{})/(?P<resource_name>{})'.format(self.name, endpoint)))
            # append resource as list
            url_patterns.append(Route(
                path='/(?P<api_name>{})/(?P<resource_name>{})/$'.format(self.name, endpoint),
                handler=resource_class.as_list(),
                methods=resource_class.route_methods(),
                name='{}_{}list'.format(self.name, endpoint).replace('/', '_')
            ))
            # append resource as detail
            url_patterns.append(Route(
                path='/(?P<api_name>{})/(?P<resource_name>{})/(?P<pk>[\w\d_.-]+)/$'.format(self.name, endpoint),
                handler=resource_class.as_detail(),
                methods=resource_class.route_methods(),
                name='{}_{}_detail'.format(self.name, endpoint).replace('/', '_')
            ))
        return url_patterns



