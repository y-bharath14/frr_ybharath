# SPDX-License-Identifier: GPL-2.0-or-later
import frrtest


class TestIsisVertexQueue(frrtest.TestMultiOut):
    program = "./test_isis_vertex_queue"


TestIsisVertexQueue.exit_cleanly()
