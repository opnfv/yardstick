# Test

from oslo_privsep import capabilities as c
from oslo_privsep import priv_context

yardstick_root = priv_context.PrivContext(
    "yardstick",
    cfg_section="yardstick_privileged",
    pypath=__name__ + ".yardstick_root",
    capabilities=[c.CAP_SYS_ADMIN],
)
