#!/usr/bin/python3

import logging

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

scale_logger = logging.getLogger("scale")


# TODO: an abstract provider-side cluster resizing interface should be created

class gce_cluster_control:

    """Abstracts cluster scaling logic. Currently will
    default and interact with the Data8 cluster using 
    GCE"""

    def __init__(self, options):
        """Needs to be initialized with options as an
        instance of settings"""
        self.options = options
        self.credentials = GoogleCredentials.get_application_default()
        self.compute = discovery.build(
            'compute', 'v1', credentials=self.credentials)
        self.zone = options.zone
        self.group = options.manager
        self.project = options.project

    def shut_down_specified_node(self, name):
        request_body = {
            "instances": [
                self.__get_node_url_from_name(name)
            ]
        }

        scale_logger.debug("Shutting down node: %s", name)

        return self.compute.instanceGroupManagers().deleteInstances(
            instanceGroupManager=self.group,
            project=self.project,
            zone=self.zone,
            body=request_body).execute()

    def add_new_node(self, cluster_size):
        """ONLY FOR CREATING NEW NODES to ensure
        new _node_number is running

        NOT FOR SCALING DOWN: random behavior expected
        TODO: Assert check that new_node_number is larger
        than current cluster size"""
        scale_logger.debug("Resizing cluster to: %d", cluster_size)

        return self.compute.instanceGroupManagers().resize(
            instanceGroupManager=self.group,
            project=self.project,
            zone=self.zone,
            size=cluster_size).execute()

    def list_managed_instances(self):
        """Lists the instances a part of the 
        specified cluster group"""
        scale_logger.debug("Gathering group: %s managed instances", self.group)
        result = self.compute.instanceGroupManagers().listManagedInstances(
            instanceGroupManager=self.group,
            project=self.project,
            zone=self.zone).execute()
        return result['managedInstances']

    def __get_node_url_from_name(self, name):
        """Gets the URL associated with the node name
        TODO: Error handling for invalid names"""
        node_url = ''
        instances = self.list_managed_instances()
        for instance in instances:
            instance_url = instance['instance']
            if name in instance_url:
                node_url = instance_url
                break
        scale_logger.debug("Node: %s has URL of: %s", name, node_url)
        return node_url
