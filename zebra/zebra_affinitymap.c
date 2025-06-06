// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * zebra affinity-map.
 *
 * Copyright 2022 6WIND S.A.
 */

#include <zebra.h>
#include "lib/if.h"
#include "lib/vrf.h"
#include "zebra/redistribute.h"
#include "zebra/zebra_affinitymap.h"

static void zebra_affinity_map_update(const char *affmap_name, uint16_t old_pos,
				      uint16_t new_pos)
{
	struct if_link_params *iflp;
	struct interface *ifp;
	struct vrf *vrf;

	RB_FOREACH (vrf, vrf_id_head, &vrfs_by_id) {
		FOR_ALL_INTERFACES (vrf, ifp) {
			iflp = if_link_params_get(ifp);
			if (!iflp)
				continue;
			if (IS_PARAM_SET(iflp, LP_EXTEND_ADM_GRP) &&
			    admin_group_get(&iflp->ext_admin_grp, old_pos)) {
				admin_group_unset(&iflp->ext_admin_grp,
						  old_pos);
				admin_group_set(&iflp->ext_admin_grp, new_pos);
			}
			if (IS_PARAM_SET(iflp, LP_ADM_GRP) &&
			    (iflp->admin_grp & (1 << old_pos))) {
				iflp->admin_grp &= ~(1 << old_pos);
				if (new_pos < 32)
					iflp->admin_grp |= 1 << new_pos;
				if (iflp->admin_grp == 0)
					UNSET_PARAM(iflp, LP_ADM_GRP);
			}
			if (if_is_operative(ifp))
				zebra_interface_parameters_update(ifp);
		}
	}
}

void zebra_affinity_map_init(void)
{
	affinity_map_init();

	affinity_map_set_update_hook(zebra_affinity_map_update);
}
