#!/usr/bin/env python
# SPDX-License-Identifier: ISC

#
# Copyright 2023 by 6WIND S.A.
#

"""
Check if BGP large-community-list works
when used as match rule in incoming route-maps.

- case 1 should deny incoming updates with large-community-list 1
bgp large-community-list 1 seq 5 permit 65001:1:1 65001:2:1
bgp large-community-list 1 seq 10 permit 65001:3:1
!
route-map r1 deny 10
 match large-community 1

route-map test deny 10
 match community 1

- case 2 should deny incoming updates with any large-community-list 1
bgp large-community-list 2 seq 10 permit 65001:12:1
!
route-map r1 deny 10
 match large-community 2 any
"""

import os
import sys
import json
import pytest
import functools

CWD = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(CWD, "../"))

# pylint: disable=C0413
from lib import topotest
from lib.topogen import Topogen, TopoRouter, get_topogen
from lib.common_config import step

pytestmark = [pytest.mark.bgpd]


def build_topo(tgen):
    for routern in range(1, 4):
        tgen.add_router("r{}".format(routern))

    switch = tgen.add_switch("s1")
    switch.add_link(tgen.gears["r1"])
    switch.add_link(tgen.gears["r2"])
    switch = tgen.add_switch("s2")
    switch.add_link(tgen.gears["r3"])
    switch.add_link(tgen.gears["r2"])


def setup_module(mod):
    tgen = Topogen(build_topo, mod.__name__)
    tgen.start_topology()

    router_list = tgen.routers()

    for i, (rname, router) in enumerate(router_list.items(), 1):
        daemon_file = "{}/{}/zebra.conf".format(CWD, rname)
        if os.path.isfile(daemon_file):
            router.load_config(TopoRouter.RD_ZEBRA, daemon_file)

        daemon_file = "{}/{}/bgpd.conf".format(CWD, rname)
        if os.path.isfile(daemon_file):
            router.load_config(TopoRouter.RD_BGP, daemon_file)

    tgen.start_router()


def teardown_module(mod):
    tgen = get_topogen()
    tgen.stop_topology()


def test_bgp_large_comm_list_match():
    tgen = get_topogen()

    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    router = tgen.gears["r2"]

    def _bgp_converge():
        output = json.loads(
            router.vtysh_cmd(
                "show bgp ipv4 unicast neighbors 192.168.0.1 filtered-routes json"
            )
        )
        expected = {
            "receivedRoutes": {
                "172.16.255.1/32": {
                    "path": "65001",
                },
                "172.16.255.3/32": {
                    "path": "65001",
                },
            }
        }
        return topotest.json_cmp(output, expected)

    step("BGP filtering check with large-community-list on R2")
    test_func = functools.partial(_bgp_converge)
    _, result = topotest.run_and_expect(test_func, None, count=60, wait=0.5)
    assert (
        result is None
    ), "Failed to filter BGP UPDATES with large-community-list on R2"


def test_bgp_large_comm_list_match_any():
    tgen = get_topogen()

    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    router = tgen.gears["r3"]

    def _bgp_converge():
        output = json.loads(
            router.vtysh_cmd(
                "show bgp ipv4 unicast neighbors 192.168.1.2 filtered-routes json"
            )
        )
        expected = {
            "receivedRoutes": {
                "172.16.255.4/32": {
                    "path": "65002 65001",
                },
            }
        }
        return topotest.json_cmp(output, expected)

    step("BGP filtering check with large-community-list on R3")
    test_func = functools.partial(_bgp_converge)
    _, result = topotest.run_and_expect(test_func, None, count=60, wait=0.5)
    assert (
        result is None
    ), "Failed to filter BGP UPDATES with large-community-list on R3"


if __name__ == "__main__":
    args = ["-s"] + sys.argv[1:]
    sys.exit(pytest.main(args))
