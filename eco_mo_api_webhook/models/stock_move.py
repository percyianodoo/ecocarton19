from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self, force_qty=False):
        """
        Block reservation auto-assignment for raw material moves of MOs
        when skip_auto_fill_qty context flag is set. This prevents move lines
        from being created with quantities that lack lot numbers.
        """
        if self.env.context.get('skip_auto_fill_qty'):
            # Filter out raw material production moves entirely
            moves_to_skip = self.filtered(lambda m: m.raw_material_production_id)
            moves_to_process = self - moves_to_skip
            if moves_to_process:
                return super(StockMove, moves_to_process)._action_assign(force_qty=force_qty)
            return
        return super()._action_assign(force_qty=force_qty)

    def _set_quantity_done(self, qty):
        """
        Block the auto-fill of quantity_done on raw material moves
        when skip_auto_fill_qty context flag is set.
        """
        if self.env.context.get('skip_auto_fill_qty') and self.raw_material_production_id:
            return
        return super()._set_quantity_done(qty)