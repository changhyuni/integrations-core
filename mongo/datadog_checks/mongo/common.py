# Source
SOURCE_TYPE_NAME = 'mongodb'

# Service check
SERVICE_CHECK_NAME = 'mongodb.can_connect'

# Replication states
"""
MongoDB replica set states, as documented at
https://docs.mongodb.org/manual/reference/replica-states/
"""
REPLSET_MEMBER_STATES = {
    0: ('STARTUP', 'Starting Up'),
    1: ('PRIMARY', 'Primary'),
    2: ('SECONDARY', 'Secondary'),
    3: ('RECOVERING', 'Recovering'),
    4: ('Fatal', 'Fatal'),  # MongoDB docs don't list this state
    5: ('STARTUP2', 'Starting up (forking threads)'),
    6: ('UNKNOWN', 'Unknown to this replset member'),
    7: ('ARBITER', 'Arbiter'),
    8: ('DOWN', 'Down'),
    9: ('ROLLBACK', 'Rollback'),
    10: ('REMOVED', 'Removed'),
}

DEFAULT_TIMEOUT = 30
ALLOWED_CUSTOM_METRICS_TYPES = ['gauge', 'rate', 'count', 'monotonic_count']
ALLOWED_CUSTOM_QUERIES_COMMANDS = ['aggregate', 'count', 'find']


def get_state_name(state):
    """Maps a mongod node state id to a human readable string."""
    if state in REPLSET_MEMBER_STATES:
        return REPLSET_MEMBER_STATES[state][0]
    else:
        return 'UNKNOWN'


def get_long_state_name(state):
    """Maps a mongod node state id to a human readable string."""
    if state in REPLSET_MEMBER_STATES:
        return REPLSET_MEMBER_STATES[state][1]
    else:
        return 'Replset state %d is unknown to the Datadog agent' % state


class Deployment(object):
    def is_principal(self):
        """In each mongo cluster there should be always one 'principal' node. One node
        that has full visibility on the user data and only one node should match the criteria.
        This is different from the 'isMaster' property as a replica set primary in a shard is considered
        as 'master' but is not 'principal' for the purpose of this integration.

        This method is used to determine if the check will collect statistics on user database, collections
        and indexes."""
        raise NotImplementedError


class MongosDeployment(Deployment):
    def is_principal(self):
        # A mongos has full visibility on the data, Datadog agents should only communicate
        # with one mongos.
        return True


class ReplicaSetDeployment(Deployment):
    def __init__(self, replset_name, replset_state, in_shard=False):
        self.replset_name = replset_name
        self.replset_state = replset_state
        self.replset_state_name = get_state_name(replset_state).lower()
        self.in_shard = in_shard
        self.is_primary = replset_state == 1

    def is_principal(self):
        # There is only ever one primary node in a replica set.
        # In case sharding is disabled, the primary can be considered the master.
        return not self.in_shard and self.is_primary


class StandaloneDeployment(Deployment):
    def is_principal(self):
        # A standalone always have full visibility.
        return True
