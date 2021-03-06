#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2018 Mozilla Corporation
"""
   script testing script
"""
# This test file calls protected methods on the vpn
# file, so, we tell pylint that we're cool with it globally:
# pylint: disable=protected-access

import unittest
import os
import sys
import re
from netaddr import IPNetwork
sys.path.insert(1, 'iamvpnlibrary')
sys.path.insert(1, 'mozdef_client')
sys.path.insert(1, 'mozdef_client_config')
import iamvpnlibrary  # pylint: disable=wrong-import-position
import netfilter_openvpn  # pylint: disable=wrong-import-position
sys.dont_write_bytecode = True


class TestNetfilterOpenVPN(unittest.TestCase):
    """ Class of tests """

    def reset_box(self):
        """
            Here we're going to assume some commands work, in an
            effort to make sure the box is happy to test with.
            This is intended to blow away debris caused by tests.
        """
        if self.library.chain_exists():
            self.library.del_chain()

    def setUp(self):
        """ Preparing test rig """
        self.assertTrue(os.getuid() == 0,
                        'Testing requires root due to ipset/iptables use.')
        self.library = netfilter_openvpn.NetfilterOpenVPN()
        _cf = self.library.configfile
        self.assertTrue(_cf.has_section('testing'), (
            'config file did not have a [testing] section'))
        # ^ this is necessary for test but not for prod, sorry
        self.assertTrue(_cf.has_option('testing', 'client_ip'),
                        'config file did not have a [testing]/client_ip')
        _client_ip = _cf.get('testing', 'client_ip')
        self.assertTrue(_cf.has_option('testing', 'client_username'),
                        'config file did not have a [testing]/client_username')
        _test_user = _cf.get('testing', 'client_username')
        self.assertIsNone(self.library.username,
                          'NetfilterOpenVPN.username was not None at init')
        self.assertIsNone(self.library.client_ip,
                          'NetfilterOpenVPN.client_ip was not None at init')
        self.assertIsNone(self.library._lock,
                          'NetfilterOpenVPN._lock was not None at init')
        self.library.set_targets(user=_test_user, client_ip=_client_ip)
        self.assertIsInstance(self.library.username, basestring)
        self.assertIsInstance(self.library.client_ip, basestring)
        self.reset_box()

    def tearDown(self):
        """ Reclaim test rig """
        self.reset_box()

    def test_init(self):
        """ Verify that the self object was initialized """
        self.assertIsInstance(netfilter_openvpn.IptablesFailure(),
                              netfilter_openvpn.IptablesFailure,
                              'IptablesFailure does not exist')
        self.assertIsInstance(netfilter_openvpn.IptablesFailure(),
                              Exception,
                              'IptablesFailure is not an Exception')
        self.assertIsInstance(netfilter_openvpn.IpsetFailure(),
                              netfilter_openvpn.IpsetFailure,
                              'IpsetFailure does not exist')
        self.assertIsInstance(netfilter_openvpn.IpsetFailure(),
                              Exception,
                              'IpsetFailure is not an Exception')
        self.assertIsInstance(self.library,
                              netfilter_openvpn.NetfilterOpenVPN,
                              'NetfilterOpenVPN did not initialize')
        self.assertIsNotNone(self.library.configfile,
                             'NetfilterOpenVPN did not get a config file')
        self.assertIsInstance(self.library.iptables_executable,
                              basestring,
                              'NetfilterOpenVPN did not get an iptables file')
        self.assertIsInstance(self.library.ipset_executable,
                              basestring,
                              'NetfilterOpenVPN did not get an ipset file')
        self.assertIsInstance(self.library.lockpath,
                              basestring,
                              'NetfilterOpenVPN did not get a lockpath file')
        self.assertIsInstance(self.library.lockwaittime,
                              int,
                              'NetfilterOpenVPN did not get a lockwaittime')
        self.assertIsInstance(self.library.lockretriesmax,
                              int,
                              'NetfilterOpenVPN did not get a lockretriesmax')

    def test_10_chain_name(self):
        """
            Verify the sanity of a chain_name string.
        """
        chain = self.library._chain_name()
        self.assertIsInstance(chain, basestring,
                              '_chain_name must be a string')
        self.assertRegexpMatches(chain, self.library.client_ip,
                                 '_chain_name must include a client IP')

    def test_10_simple_locking(self):
        """
            Make a lock, release a lock
        """
        self.assertIsNone(self.library._lock)
        self.assertTrue(self.library.acquire_lock())
        self.assertIsInstance(self.library._lock, file)
        self.assertTrue(self.library.free_lock())
        self.assertIsNone(self.library._lock)

    def test_failure_locking(self):
        """
            Make a lock, try making another lock and failing,
            then release a lock
        """
        pass
        # This case should be written.
        # The problem stems from the need to make this unittest be
        # multiprocessor.  Making 2 locks from this test will succeed
        # because it's the same thing getting the same lock.
        #
        # We'd need to fork and lock.  And then, the other process
        # try to fork and lock, and then everyone work out how to
        # unlock.  In absence of writing that, we (*sigh*) assume
        # that locking works.

    def test_20_get_acls_for_user(self):
        """
            Verify the get_acls_for_user returns.  This is mostly
            checking that we didn't do something stupid massaging
            the values returned from iamvpnlibrary.
        """
        # sorted list of parsedacl
        acls = self.library.get_acls_for_user()
        self.assertIsInstance(acls, list,
                              'get_acls_for_user must return a list')
        # 5 picked at random for "someone likely has that many acls
        self.assertGreater(len(acls), 5,
                           'get_acls_for_user was a too-short list?')
        acl1 = acls[0]
        acl2 = acls[4]
        self.assertIsInstance(acl1, iamvpnlibrary.iamvpnbase.ParsedACL,
                              ('get_acls_for_user did not contain '
                               'ParsedACLs'))
        self.assertIsInstance(acl1.rule, basestring,
                              'ParsedACL.rule was not a string')
        self.assertIsInstance(acl1.address, IPNetwork,
                              'ParsedACL.address was not an IPNetwork')
        self.assertIsInstance(acl1.portstring, basestring,
                              'ParsedACL.portstring was not a string')
        self.assertIsInstance(acl1.description, basestring,
                              'ParsedACL.description was not a string')
        # The ACLs should be sorted large-to-small:
        self.assertGreaterEqual(acl1.address.size,
                                acl2.address.size,
                                'get_acls_for_user list was not size-sorted')

    def test_30_iptables(self):
        """
            This tests that an iptables call has the correct return values
            It's a fairly uninteresting test suite, complexity-wise.
        """
        _tmp = self.library.iptables_executable
        self.library.iptables_executable = '/tmp/notascript'
        with self.assertRaises(netfilter_openvpn.IptablesFailure):
            self.library.iptables('-L >/dev/null 2>&1')
        self.library.iptables_executable = _tmp

        self.assertTrue(self.library.iptables('-L', False))
        self.assertTrue(self.library.iptables('-L >/dev/null 2>&1', True))
        self.assertFalse(self.library.iptables('-L garbage_here', False))
        with self.assertRaises(netfilter_openvpn.IptablesFailure):
            self.library.iptables('-L garbage_here >/dev/null 2>&1', True)

    def test_30_ipset(self):
        """
            This tests that an ipset call has the correct return values
            It's a fairly uninteresting test suite, complexity-wise.
        """
        _tmp = self.library.ipset_executable
        self.library.ipset_executable = '/tmp/notascript'
        with self.assertRaises(netfilter_openvpn.IpsetFailure):
            self.library.ipset('--list >/dev/null 2>&1')
        self.library.ipset_executable = _tmp

        self.assertTrue(self.library.ipset('--list', False))
        self.assertTrue(self.library.ipset('--list >/dev/null 2>&1', True))
        self.assertFalse(self.library.ipset('--list garbage_here', False))
        with self.assertRaises(netfilter_openvpn.IpsetFailure):
            self.library.ipset('--list garbage_here >/dev/null 2>&1', True)

    def test_40_build_fw_rule_iptables(self):
        """
            This test pops in rules that shoule become iptables, and
            makes sure they end up there, and not in ipset.
        """
        chain = self.library._chain_name()
        _junk_dest_address = '1.2.3.4'
        _multiports1 = '80,443'
        _multiports2 = '22'
        self.library.iptables('-N ' + self.library.client_ip)
        self.library.ipset('--create ' + self.library.client_ip + ' nethash')
        iptables_acl1 = iamvpnlibrary.iamvpnbase.ParsedACL(
            rule='', address=_junk_dest_address, portstring=_multiports1,
            description='')
        self.library._build_firewall_rule(
            self.library.client_ip, self.library.client_ip,
            'tcp', iptables_acl1)
        iptables_acl2 = iamvpnlibrary.iamvpnbase.ParsedACL(
            rule='blah', address=_junk_dest_address, portstring=_multiports2,
            description='ssh test')
        self.library._build_firewall_rule(
            self.library.client_ip, self.library.client_ip,
            'tcp', iptables_acl2)
        self.assertFalse(
            self.library.ipset('test ' + self.library.client_ip + ' ' +
                               _junk_dest_address + '>/dev/null 2>&1', False),
            'ipset was not empty when it should have been')
        # Yes, these are awful checks trying to make sure there's matches.
        # Sorry.  Precision needed.
        self.assertTrue(
            self.library.iptables('-C ' + chain + ' -s ' +
                                  self.library.client_ip + ' -d ' +
                                  _junk_dest_address +
                                  ' -p tcp -m multiport --dports ' +
                                  _multiports1 + ' -j ACCEPT', False))
        commentstring = self.library.username + ':blah ACL ssh test'
        self.assertTrue(
            self.library.iptables('-C ' + chain + ' -s ' +
                                  self.library.client_ip + ' -d ' +
                                  _junk_dest_address +
                                  ' -p tcp -m multiport --dports ' +
                                  _multiports2 + ' -m comment --comment "' +
                                  commentstring + '" -j ACCEPT', False))

    def test_40_build_fw_rule_ipset(self):
        """
            This test pops in rules that shoule become ipset rules, and
            makes sure they end up there, and not in iptables.
        """
        chain = self.library._chain_name()
        _junk_dest_address = '1.2.3.4'
        self.library.iptables('-N ' + self.library.client_ip)
        self.library.ipset('--create ' + self.library.client_ip + ' nethash')
        ipset_acl = iamvpnlibrary.iamvpnbase.ParsedACL(
            rule='', address=_junk_dest_address, portstring='',
            description='')
        self.library._build_firewall_rule(
            self.library.client_ip, self.library.client_ip, '', ipset_acl)
        self.assertTrue(
            self.library.ipset('test ' + self.library.client_ip + ' ' +
                               _junk_dest_address + '>/dev/null 2>&1', False),
            'ipset did not contain a net when added')
        # This is a hack.  No rules should be created in iptables.  So try to
        # delete rule 1.  If this succeeds, that's bad.  If it fails, yay.
        self.assertFalse(
            self.library.iptables('-D ' + chain + ' 1', False),
            'There were rules created in iptables when there should not be.')

    def test_50_create_user_rules(self):
        """
            Test creates a chain set for a test user
        """
        acls = self.library.get_acls_for_user()
        self.library.create_user_rules(acls)
        self.assertTrue(self.library.chain_exists())
        # This will have made ipset and iptables for a user.
        # Testing here is difficult, as the contents depend upon
        # what the test user is allowed to do.  So we are actually left
        # with a very deficient test here.  Patches welcome for
        # detection of other cases.
        #
        # This is a runthrough of commenting to make vpn-fw-find-user happy.
        command = '{ipt} -L -v -n'.format(
            ipt=self.library.iptables_executable)
        # IMPROVEME os calls
        _all_rules = os.popen(command).read().splitlines()
        _user_rules = [rule for rule in _all_rules
                       if self.library.username in rule]
        _matchset_rules = [rule for rule in _user_rules if 'match-set' in rule]
        self.assertEqual(len(_matchset_rules), 1,
                         'Deployed rules for user needs one match-set rule')
        self.assertRegexpMatches(_matchset_rules[0], ';',
                                 'No semicolons found in match-set comment')

    def test_80_safety_blocks(self):
        """
            Test the insert/remove of blocking rules
        """
        self.assertFalse(
            self.library.iptables('-C FORWARD -s {ip} -j DROP'.format(
                ip=self.library.client_ip), False),
            'OS had a blocking rule in place before we began tests')
        self.library.remove_safety_block()
        self.assertFalse(
            self.library.iptables('-C FORWARD -s {ip} -j DROP'.format(
                ip=self.library.client_ip), False),
            'Did not quietly "remove nothing"')
        self.library.add_safety_block()
        self.assertTrue(
            self.library.iptables('-C FORWARD -s {ip} -j DROP'.format(
                ip=self.library.client_ip), False),
            'OS did not gain a blocking rule as expected')
        self.library.remove_safety_block()
        self.assertFalse(
            self.library.iptables('-C FORWARD -s {ip} -j DROP'.format(
                ip=self.library.client_ip), False),
            'Did not remove blocking rule')

    def test_90_chains(self):
        """
            This builds a chain and tears it down, making sure it appears
            and disappears.
            This is the soup-to-nuts of the main section of the script.
            It is not an interesting debugger, but it does replicate the
            buildup/teardown of the whole script.
        """
        self.assertFalse(self.library.chain_exists())
        self.library.add_chain()
        self.assertTrue(self.library.chain_exists())
        self.library.del_chain()
        self.assertFalse(self.library.chain_exists())
        # This test has the same problem as test_50_create_user_rules
        # Without knowing the rules of a person, we can't readily
        # verify their data.  All the next checks have the same problem.

    def test_91_chains(self):
        """
            This builds a chain, does an update, and tears it down,
            making sure it appears and disappears.
        """
        self.assertFalse(self.library.chain_exists())
        self.library.add_chain()
        self.assertTrue(self.library.chain_exists())
        self.library.update_chain()
        self.assertTrue(self.library.chain_exists())
        self.library.del_chain()
        self.assertFalse(self.library.chain_exists())

    def test_92_chains(self):
        """
            This builds a chain, tries a bogus add, and tears it down,
            making sure it appears and disappears.
        """
        self.assertFalse(self.library.chain_exists())
        self.library.add_chain()
        self.assertTrue(self.library.chain_exists())
        self.library.add_chain()
        self.assertTrue(self.library.chain_exists())
        self.library.del_chain()
        self.assertFalse(self.library.chain_exists())

    def test_93_chains(self):
        """
            This deletes a chain that isn't there.
        """
        self.assertFalse(self.library.chain_exists())
        self.library.del_chain()
        self.assertFalse(self.library.chain_exists())
