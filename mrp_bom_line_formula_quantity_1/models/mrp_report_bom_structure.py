# -*- coding: utf-8 -*-

from collections import defaultdict, OrderedDict
from datetime import date, datetime, time, timedelta
import json

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_round, format_date, float_is_zero, float_repr
from odoo.exceptions import UserError


class ReportBomStructure(models.AbstractModel):
    _inherit = "report.mrp.report_bom_structure"

    @api.model
    def _get_bom_data(self, bom, warehouse, product=False, line_qty=False, bom_line=False, level=0, parent_bom=False,
                      parent_product=False, index=0, product_info=False, ignore_stock=False,
                      simulated_leaves_per_workcenter=False):
        """ Gets recursively the BoM and all its subassemblies and computes availibility estimations for each component and their disponibility in stock.
            Accepts specific keys in context that will affect the data computed :
            - 'minimized': Will cut all data not required to compute availability estimations.
            - 'from_date': Gives a single value for 'today' across the functions, as well as using this date in products quantity computes.
        """
        is_minimized = self.env.context.get('minimized', False)
        if not product:
            product = bom.product_id or bom.product_tmpl_id.product_variant_id
        if line_qty is False:
            line_qty = bom.product_qty
        if not product_info:
            product_info = {}
        if simulated_leaves_per_workcenter is False:
            simulated_leaves_per_workcenter = defaultdict(list)

        company = bom.company_id or self.env.company
        current_quantity = line_qty
        if bom_line:
            current_quantity = bom_line.product_uom_id._compute_quantity(line_qty, bom.product_uom_id) or 0

        has_attachments = False
        if not is_minimized:
            if product:
                has_attachments = self.env['product.document'].search_count(
                    ['&', '&', ('attached_on_mrp', '=', 'bom'), ('active', '=', 't'), '|', '&',
                     ('res_model', '=', 'product.product'),
                     ('res_id', '=', product.id), '&', ('res_model', '=', 'product.template'),
                     ('res_id', '=', product.product_tmpl_id.id)], limit=1) > 0
            else:
                # Use the product template instead of the variant
                has_attachments = self.env['product.document'].search_count(
                    ['&', '&', ('attached_on_mrp', '=', 'bom'), ('active', '=', 't'),
                     '&', ('res_model', '=', 'product.template'), ('res_id', '=', bom.product_tmpl_id.id)], limit=1) > 0

        key = product.id
        bom_key = bom.id
        qty_product_uom = bom.product_uom_id._compute_quantity(current_quantity,
                                                               product.uom_id or bom.product_tmpl_id.uom_id)
        self._update_product_info(product, bom_key, product_info, warehouse, qty_product_uom, bom=bom,
                                  parent_bom=parent_bom, parent_product=parent_product)
        route_info = product_info[key].get(bom_key, {})
        quantities_info = {}
        if not ignore_stock:
            # Useless to compute quantities_info if it's not going to be used later on
            quantities_info = self._get_quantities_info(product, bom.product_uom_id, product_info, parent_bom,
                                                        parent_product)

        bom_report_line = {
            'index': index,
            'bom': bom,
            'bom_id': bom and bom.id or False,
            'bom_code': bom and bom.code or False,
            'type': 'bom',
            'is_storable': product.is_storable,
            'quantity': current_quantity,
            'quantity_available': quantities_info.get('free_qty') or 0,
            'quantity_on_hand': quantities_info.get('on_hand_qty') or 0,
            'quantity_forecasted': quantities_info.get('forecasted_qty') or 0,
            'free_to_manufacture_qty': quantities_info.get('free_to_manufacture_qty') or 0,
            'base_bom_line_qty': bom_line.product_qty if bom_line else False,
            # bom_line isn't defined only for the top-level product
            'name': product.display_name or bom.product_tmpl_id.display_name,
            'uom': bom.product_uom_id if bom else product.uom_id,
            'uom_name': bom.product_uom_id.name if bom else product.uom_id.name,
            'route_type': route_info.get('route_type', ''),
            'route_name': route_info.get('route_name', ''),
            'route_detail': route_info.get('route_detail', ''),
            'route_alert': route_info.get('route_alert', False),
            'currency': company.currency_id,
            'currency_id': company.currency_id.id,
            'product': product,
            'product_id': product.id,
            'product_template_id': product.product_tmpl_id.id,
            'link_id': (product.id if product.product_variant_count > 1 else product.product_tmpl_id.id) or bom.product_tmpl_id.id,
            'link_model': 'product.product' if product.product_variant_count > 1 else 'product.template',
            'code': bom and bom.display_name or '',
            'bom_cost': 0,
            'level': level or 0,
            'has_attachments': has_attachments,
            'phantom_bom': bom.type == 'phantom',
            'parent_id': parent_bom and parent_bom.id or False,
        }

        components = []
        no_bom_lines = self.env['mrp.bom.line']
        line_quantities = {}
        for line in bom.bom_line_ids:
            if product and line._skip_bom_line(product):
                continue
            line_quantity = (current_quantity / (bom.product_qty or 1.0)) * line.product_qty

            # custom code start >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

            if line.quantity_formula:
                computed_quantity = line._eval_quantity_formula(
                    product=product,
                    product_uom=bom.product_uom_id,
                    product_uom_qty=current_quantity,
                    production=self.env['mrp.production'],
                    operation_id=False,
                )
                if computed_quantity is not None:
                    line_quantity = (current_quantity / (bom.product_qty or 1.0)) * computed_quantity

            # custom code end >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.

            line_quantities[line.id] = line_quantity
            if not line.child_bom_id:
                no_bom_lines |= line
                # Update product_info for all the components before computing closest forecasted.
                qty_product_uom = line.product_uom_id._compute_quantity(line_quantity, line.product_id.uom_id)
                self._update_product_info(line.product_id, bom.id, product_info, warehouse, qty_product_uom, bom=False,
                                          parent_bom=bom, parent_product=product)
        components_closest_forecasted = self._get_components_closest_forecasted(no_bom_lines, line_quantities, bom,
                                                                                product_info, product, ignore_stock)
        for component_index, line in enumerate(bom.bom_line_ids):
            new_index = f"{index}{component_index}"
            if product and line._skip_bom_line(product):
                continue
            line_quantity = line_quantities.get(line.id, 0.0)
            if line.child_bom_id:
                component = self._get_bom_data(line.child_bom_id, warehouse, line.product_id, line_quantity,
                                               bom_line=line, level=level + 1, parent_bom=bom,
                                               parent_product=product, index=new_index, product_info=product_info,
                                               ignore_stock=ignore_stock,
                                               simulated_leaves_per_workcenter=simulated_leaves_per_workcenter)
            else:
                component = self.with_context(
                    components_closest_forecasted=components_closest_forecasted,
                )._get_component_data(bom, product, warehouse, line, line_quantity, level + 1, new_index, product_info,
                                      ignore_stock)
            for component_bom in components:
                if component['product_id'] == component_bom['product_id'] and component['uom'].id == component_bom[
                    'uom'].id:
                    self._merge_components(component_bom, component)
                    break
            else:
                components.append(component)
            bom_report_line['bom_cost'] += component['bom_cost']
        for component in components:
            if component['is_storable']:
                if missing_qty := max(component['quantity'] - component['quantity_forecasted'], 0):
                    missing_qty = float_repr(missing_qty, self.env['decimal.precision'].precision_get('Product Unit'))
                    route_name = component['route_name'] or _('Order')
                    component['status'] = _("%(qty)s To %(route)s", qty=missing_qty, route=route_name)
        bom_report_line['components'] = components
        bom_report_line['producible_qty'] = self._compute_current_production_capacity(bom_report_line)

        availabilities = self._get_availabilities(product, current_quantity, product_info, bom_key, quantities_info,
                                                  level, ignore_stock, components, report_line=bom_report_line)
        # in case of subcontracting, lead_time will be calculated with components availability delay
        bom_report_line['lead_time'] = route_info.get('lead_time', False)
        bom_report_line['manufacture_delay'] = route_info.get('manufacture_delay', False)
        bom_report_line.update(availabilities)

        if level == 0:
            if bom_report_line['producible_qty'] > 0:
                bom_report_line['status'] = _("%(qty)s Ready To Produce", qty=bom_report_line['producible_qty'])
            else:
                bom_report_line['status'] = _("No Ready To Produce")
        elif missing_qty := max(bom_report_line['quantity'] - bom_report_line['quantity_available'], 0):
            missing_qty = float_repr(missing_qty, self.env['decimal.precision'].precision_get('Product Unit'))
            route_name = bom_report_line['route_name'] or _('Order')
            bom_report_line['status'] = _("%(qty)s To %(route)s", qty=missing_qty, route=route_name)

        if not is_minimized:

            operations = self._get_operation_line(product, bom, float_round(current_quantity, precision_digits=self.env[
                'decimal.precision'].precision_get('Product Unit'), rounding_method='UP'), level + 1, index,
                                                  bom_report_line, simulated_leaves_per_workcenter)
            bom_report_line['operations'] = operations
            bom_report_line['operations_cost'] = sum(op['bom_cost'] for op in operations)
            bom_report_line['operations_time'] = sum(op['quantity'] for op in operations)
            bom_report_line['operations_delay'] = max((op['availability_delay'] for op in operations), default=0)
            if 'simulated' in bom_report_line:
                bom_report_line['availability_state'] = 'estimated'
                max_component_delay = bom_report_line['max_component_delay']
                bom_report_line['availability_delay'] = max_component_delay + max(bom.produce_delay,
                                                                                  bom_report_line['operations_delay'])
                bom_report_line['availability_display'] = self._format_date_display(
                    bom_report_line['availability_state'], bom_report_line['availability_delay'])
            bom_report_line['bom_cost'] += bom_report_line['operations_cost']

            byproducts, byproduct_cost_portion = self._get_byproducts_lines(product, bom, current_quantity, level + 1,
                                                                            bom_report_line['bom_cost'], index)
            bom_report_line['byproducts'] = byproducts
            bom_report_line['cost_share'] = float_round(1 - byproduct_cost_portion, precision_rounding=0.0001)
            bom_report_line['byproducts_cost'] = sum(byproduct['bom_cost'] for byproduct in byproducts)
            bom_report_line['byproducts_total'] = sum(byproduct['quantity'] for byproduct in byproducts)
            bom_report_line['bom_cost'] *= bom_report_line['cost_share']

        bom_report_line['foldable'] = len(bom.operation_ids) > 0 or (
                len(bom_report_line['components']) > 0 and level > 0) or any(
            component.get('foldable', False) for component in bom_report_line['components'])

        if level == 0:
            # Gives a unique key for the first line that indicates if product is ready for production right now.
            bom_report_line['components_available'] = all([c['stock_avail_state'] == 'available' for c in components])
        return bom_report_line
