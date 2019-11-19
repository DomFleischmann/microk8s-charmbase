from juju.charm import CharmBase, CharmEvents, RelationUnitEvent
from juju.framework import (
    Event,
    EventBase,
    StoredState,
)

import subprocess
import collections
import yaml
import base64

from pathlib import Path

from enum import (
    Enum,
    unique,
)

class Microk8sReadyEvent(EventBase):
    pass


class Microk8sCharmEvents(CharmEvents):
    micork8s_ready = Event(Microk8sReadyEvent)

class Charm(CharmBase):

    on = Microk8sCharmEvents()


    state = StoredState()


    def __init__(self, *args):
        super().__init__(*args)

        self.framework.observe(self.on.install, self)
        self.framework.observe(self.on.start, self)


    def on_install(self, event):
        snap_install('microk8s')
        log(f'on_install: installing')

    def on_start(self, event):
        log(f'on_start: starting')

        if not _is_snap_installed('microk8s'):
            event.defer()
            self.state.ready = False
            return 
        
        self.state.ready = True
        subprocess.call(
            'sudo usermod -a -G microk8s ubuntu',
            shell=True
        )
        apt_install(['hello'])
        status_set('active','Ready!')

def status_set(workload_state, message):
    """Set the workload state with a message

    Use status-set to set the workload state with a message which is visible
    to the user via juju status.

    workload_state -- valid juju workload state.
    message        -- status update message
    """
    valid_states = ['maintenance', 'blocked', 'waiting', 'active']

    if workload_state not in valid_states:
        raise ValueError(
            '{!r} is not a valid workload state'.format(workload_state)
        )

    subprocess.check_call(['status-set', workload_state, message])

def log(message, level=None):
    """Write a message to the juju log"""
    command = ['juju-log']
    if level:
        command += ['-l', level]
    if not isinstance(message, str):
        message = repr(message)

    # https://elixir.bootlin.com/linux/latest/source/include/uapi/linux/binfmts.h
    # PAGE_SIZE * 32 = 4096 * 32
    MAX_ARG_STRLEN = 131072
    command += [message[:MAX_ARG_STRLEN]]
    # Missing juju-log should not cause failures in unit tests
    # Send log output to stderr
    subprocess.call(command)

def apt_install(packages, options=None):
    """Install one or more packages.

    packages -- package(s) to install.
    options -- a list of apt options to use.
    """
    if options is None:
        options = ['--option=Dpkg::Options::=--force-confold']

    command = ['apt-get', '--assume-yes']
    command.extend(options)
    command.append('install')

    if isinstance(packages, collections.abc.Sequence):
        command.extend(packages)
    else:
        raise ValueError(f'Invalid type was used for the "packages" argument: {type(packages)} instead of str')

    log("Installing {} with options: {}".format(packages, options))

    subprocess.check_call(command)

def snap_install(snapname, **kw):
    cmd = ['snap', 'install']
    cmd.extend(_snap_args(**kw))
    cmd.append(snapname)
    log('Installing {} from store'.format(snapname))
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)

def _is_snap_installed(snapname):
    out = subprocess.check_output["which", "microk8s"]
    if out:
        return True
    else:
        return False

def _snap_args(channel='stable', devmode=False, jailmode=False,
               dangerous=False, force_dangerous=False, connect=None,
               classic=False, revision=None):
    yield '--channel={}'.format(channel)
    if devmode is True:
        yield '--devmode'
    if jailmode is True:
        yield '--jailmode'
    if force_dangerous is True or dangerous is True:
        yield '--dangerous'
    if classic is True:
        yield '--classic'
    if revision is not None:
        yield '--revision={}'.format(revision)
