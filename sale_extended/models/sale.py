from odoo import models, _, api, fields
from datetime import datetime, time
from odoo.addons.sale_stock.models.sale_order import SaleOrder

# Import the ORIGINAL SaleOrder from sale module, not sale_stock
from odoo.addons.sale.models.sale_order import SaleOrder as OriginalSaleOrder

SALE_ORDER_STATE = [
    ('draft', "Quotation"),
    ('sent', "Quotation Sent"),
    ('confirmed', 'Confirmed'),
    ('sale', "Sales Order"),
    ('cancel', "Cancelled"),
]
# Store the original method from the base sale module
original_action_confirm = OriginalSaleOrder._action_confirm


def _action_confirm(self):
    # Get selected line ID from context
    selected_so_line_id = self.env.context.get('selected_so_line_id')
    if selected_so_line_id:
        selected_line = self.order_line.filtered(
            lambda line: line.id == selected_so_line_id
        )
        if selected_line:
            selected_line._action_launch_stock_rule()

            context_without_selection = dict(self.env.context)
            context_without_selection.pop('selected_so_line_id', None)
            self.env.context = context_without_selection

            return original_action_confirm(self)

    # Default behavior - process all lines
    return original_action_confirm(self)


SaleOrder._action_confirm = _action_confirm


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sub_mo_counter = fields.Integer(default=0, copy=False)
    mo_calc_ids = fields.One2many("mo.calculation", "sale_id", string="MO Calculations", copy=False)
    display_mo_calculation_button = fields.Boolean(string="Dispaly Mo calculation button?",
                                                   compute="_compute_display_mo_calculation_button", store=True,
                                                   copy=False)

    state = fields.Selection(
        selection=SALE_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')

    def custom_action_so_confirm(self):
        containings_all_normal_product = True

        for line in self.order_line:
            # create picking for the normal type products
            if (not line.product_id.route_ids) or line.product_id.route_ids.filtered(lambda r: r.name not in ['Replenish on Order (MTO)','Manufacture']):
                line.state ='sale'
                # containings_all_normal_product = False
                line._action_launch_stock_rule()
            else:
                containings_all_normal_product = False

        if containings_all_normal_product:
            self.state = 'sale'
        else:
            self.state = 'confirmed'

    @api.depends('order_line')
    def _compute_display_mo_calculation_button(self):
        for so in self:
            display = True
            if len(so.order_line) == 1:
                for line in so.order_line:
                    if line.product_id:
                        if not line.product_id.route_ids or len(line.product_id.route_ids.filtered(lambda r: r.name in ['Buy','Dropship'])) == 1:
                            display = False
            so.display_mo_calculation_button = display

    def action_view_mo_calculations(self):
        self.ensure_one()
        action = self.env.ref("sale_extended.action_mo_calculation").read()[0]
        action["domain"] = [("sale_id", "=", self.id)]
        action["context"] = {"default_sale_id": self.id}
        return action

    def action_generate_mo_calculations(self):
        for order in self:
            for line in order.order_line:
                if not (line.product_id.route_ids.filtered(lambda r: r.name == 'Buy') or not line.product_id.route_ids):
                    mo_cal_ids = self.env["mo.calculation"].create({
                        "sale_id": order.id,
                        "sale_line_id": line.id,
                    })
                    order.mo_calc_ids = mo_cal_ids

    # procurement_group_id.stock_move_ids.created_production_id.procurement_group_id !TODO curency commented gettings errors ya
    @api.depends('mrp_production_ids')
    def _compute_mrp_production_ids(self):
        super()._compute_mrp_production_ids()  # Call Odoo's original logic first

        for sale in self:
            root_mos = sale.mrp_production_ids
            all_mos = self.env['mrp.production'].browse()
            to_visit = root_mos

            while to_visit:
                next_mos = self.env['mrp.production'].browse()
                for mo in to_visit:
                    if mo in all_mos:
                        continue
                    all_mos |= mo

                    # Recursively find child MOs
                    procurement_moves = mo.procurement_group_id.stock_move_ids
                    child_moves = procurement_moves.move_orig_ids
                    child_mos = (
                            (
                                    procurement_moves | child_moves).created_production_id.procurement_group_id.mrp_production_ids
                            | child_moves.production_id
                    ).filtered(lambda m: m not in all_mos)

                    next_mos |= child_mos

                to_visit = next_mos

            # Update with all collected MOs (including root + recursive)
            sale.mrp_production_ids = all_mos
            sale.mrp_production_count = len(all_mos)

    # def action_confirm(self):
    #     ctx = self.env.context.copy()
    #     ctx.update({"skip_procurement": True})
    #     res = super(SaleOrder, self.with_context(ctx)).action_confirm()
    #     return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # 'product_uom' !TODO currently commenteds ya gettinges errors ya
    @api.depends('is_storable', 'product_uom_qty', 'qty_delivered', 'state', 'move_ids')
    def _compute_qty_to_deliver(self):
        """Compute the visibility of the inventory widget."""
        for line in self:
            line.qty_to_deliver = line.product_uom_qty - line.qty_delivered
            if line.state in ('draft', 'sent', 'sale','confirmed') and line.is_storable and line.product_uom and line.qty_to_deliver > 0:
                if line.state == 'sale' and not line.move_ids:
                    line.display_qty_widget = False
                else:
                    line.display_qty_widget = True
            else:
                line.display_qty_widget = False

class ProductProduct(models.Model):
    _inherit = 'product.template'

    formula = fields.Char(string="MO Calculation Formula (use # for qty)")
