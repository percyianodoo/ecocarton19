# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def _get_duration_expected(self, alternative_workcenter=False, ratio=1):
        self.ensure_one()
        duration = super()._get_duration_expected(
            alternative_workcenter=alternative_workcenter,
            ratio=ratio,
        )
        capacity, time_start, time_stop = self.workcenter_id._get_capacity(
            self.product_id,
            self.product_id.uom_id,
        )
        setup_time = time_start + time_stop
        production_duration = max(duration - setup_time, 0)
        pieces = self.operation_id.pieces_per_cycle or 1.0
        result = setup_time + (production_duration / pieces)
        _logger.warning(
            "Duration=%s Setup=%s Production=%s Pieces=%s Result=%s",
            duration,
            setup_time,
            production_duration,
            pieces,
            result,
        )
        return result


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    pieces_per_cycle = fields.Float(
        string='Pieces Produced',
        default=100.0,
        tracking=True,
    )
