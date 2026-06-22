from odoo import models, fields, api
import re


class MoCalculationWizard(models.TransientModel):
    _name = 'mo.calculation.wizard'
    _description = 'MO Calculation Wizard'

    calc_id = fields.Many2one('mo.calculation', string="Calculation", required=True)
    line_ids = fields.One2many('mo.calculation.wizard.line', 'wizard_id', string="MOs")

    def action_recalculate(self):
        self.line_ids._recalculate_lines()
        for line in self.line_ids:
            if line.production_id:
                line.production_id.product_qty = line.product_qty


        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mo.calculation.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }


class MoCalculationWizardLine(models.TransientModel):
    _name = 'mo.calculation.wizard.line'
    _description = 'MO Calculation Wizard Line'

    wizard_id = fields.Many2one('mo.calculation.wizard', string="Wizard")
    production_id = fields.Many2one('mrp.production', string="Manufacturing Order", readonly=True)
    product_id = fields.Many2one(related="production_id.product_id", readonly=True)
    bom_id = fields.Many2one(related="production_id.bom_id", readonly=True)

    # result_qty = fields.Float(string="Result Qty")
    formula = fields.Char(string="Formula (Use #)")
    product_qty = fields.Float(related='production_id.product_uom_qty',string="Product Qty",readonly=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            production_id = vals.get('production_id')
            if production_id:
                production = self.env['mrp.production'].browse(production_id)
                if not vals.get('formula'):
                    vals['formula'] = production.product_id.formula or ''

        return super().create(vals_list)


    def _recalculate_lines(self):
        """Compute product_qty based on formulas and wastage"""
        for wizard in self.mapped('wizard_id'):
            base_value = wizard.calc_id.x_studio_wastage_calculation or 0.0
            # current_value = base_value
            # current_value = line.product_qty
            qty_change_wizard_obj = self.env['change.production.qty'].sudo()
            number_pattern = r"-?\d+(?:\.\d+)?"
            running_value = 0
            for idx, line in enumerate(wizard.line_ids):



                mo_id = line.production_id
                formula_result = 0
                prev_line = wizard.line_ids[idx - 1]
                prev_mo_id = prev_line.production_id
                new_qty = wizard.calc_id.x_studio_wastage_calculation
                is_prev_line_fixed_qty_mo = False
                if prev_line:
                    prev_source_mo_bom_components_id = prev_line.production_id._get_sources().bom_id.bom_line_ids.filtered(
                        lambda l: l.product_id.id == prev_line.production_id.product_id.id)
                    if prev_source_mo_bom_components_id.quantity_formula:
                        is_prev_line_fixed_qty_mo = True
                #     new_qty = prev_line.product_qty
                #     previoussource_mo_bom_components_id = prev_mo_id._get_sources().bom_id.bom_line_ids.filtered(
                #         lambda l: l.product_id.id == prev_mo_id.product_id.id)
                #     if
                is_fixed_qty_mo = False
                source_mo_bom_components_id = mo_id._get_sources().bom_id.bom_line_ids.filtered(
                    lambda l: l.product_id.id == mo_id.product_id.id)
                if source_mo_bom_components_id.quantity_formula:
                    is_fixed_qty_mo = True


                if not is_fixed_qty_mo:
                    if prev_line.formula and not is_prev_line_fixed_qty_mo:
                        try:
                            # First pass: Replace # with actual quantity
                            expr = prev_line.formula.replace('#', str(prev_line.product_qty))

                            # Second pass: Process all percentages in the expression
                            def calculate_percentage(match):
                                # Extract the number before %
                                percent_value = float(match.group(1))
                                # Calculate percentage of the original quantity
                                return str((percent_value / 100) * prev_line.product_qty)

                            # expr = re.sub(r'(\d+(\.\d+)?)%',
                            #               lambda m: str(float(m.group(1)) / 100),
                            #               expr)
                                # Process all percentages in the expression
                            expr = re.sub(r'(\d+(?:\.\d+)?)%', calculate_percentage, expr)
                            formula_result = eval(expr, {"__builtins__": {}})
                        except Exception:
                            formula_result = formula_result
                        running_value = formula_result
                        new_qty = running_value

                    else:
                        # running_value = new_qty
                        new_qty = running_value or wizard.calc_id.x_studio_wastage_calculation
                    # if mo_id._get_sources():
                    #     source_mo_bom_components_id = mo_id._get_sources().bom_id.bom_line_ids.filtered(
                    #         lambda l: l.product_id.id == mo_id.product_id.id)
                    #     if source_mo_bom_components_id.quantity_formula:
                    #         res = re.findall(number_pattern, source_mo_bom_components_id.quantity_formula)
                    #         if len(res)>=1:
                    #             qty = float(res[0])
                    #             # components.with_context(bypass_procurement_creation=True,no_procurement=True).product_uom_qty = new_qty
                    #             new_qty = qty
                    #     else:
                    #         if formula_result:
                    #             new_qty = formula_result
                    #         else:
                    #             new_qty = new_qty
                    #     # for s_mo_components in mo_id._get_sources().move_raw_ids:
                    #     #     if mo_id.product_id.id == s_mo_components.product_id.id:
                    # else:
                    #     if formula_result:
                    #         new_qty = formula_result
                    #     else:
                    #         new_qty = new_qty
                else:
                    if source_mo_bom_components_id.quantity_formula:
                        res = re.findall(number_pattern, source_mo_bom_components_id.quantity_formula)
                        if len(res)>=1:
                            qty = float(res[0])
                            new_qty = qty
                # current_value = line.product_qty
                # if idx == 0:
                #     print("Hiieas")
                #     # line.product_qty = base_value
                # #     if not line.formula:
                # #         line.formula = line.production_id.product_id.formula or ''
                # # current_value = line.product_qty
                # else:
                #     prev_line = wizard.line_ids[idx - 1]
                #     formula_to_use = prev_line.formula or ''
                #     result = current_value
                #     if formula_to_use:
                #         try:
                #             expr = formula_to_use.replace('#', str(current_value))
                #
                #             expr = re.sub(r'(\d+(\.\d+)?)%',
                #                           lambda m: str(float(m.group(1)) / 100),
                #                           expr)
                #
                #             result = eval(expr, {"__builtins__": {}})
                #         except Exception:
                #             result = current_value
                #
                #     line.product_qty = result
                #     current_value = result


                # for components
                # qty = line.product_qty
                # if line.production_id._get_sources():
                #     for components in line.production_id._get_sources().move_raw_ids:
                #         if line.production_id.product_id.id == components.product_id.id:
                #             qty = components.product_uom_qty
                #             break


                update_quantity_wizard = qty_change_wizard_obj.create({
                    'mo_id':line.production_id.id,
                    'product_qty':new_qty
                })
                ctx = self._context.copy()
                ctx.update({'bypass_procurement_creation':True})
                # self._context = ctx
                # self.env.context.get('no_procurement',)
                update_quantity_wizard.with_context(bypass_procurement_creation=True,no_procurement=True).change_prod_qty()



                # # Setting up the Manufacturing order's products_uom_qty if componets containings ans any formula
                # for components in line.production_id.move_raw_ids:
                    #
                    # # components.
                    #
                    # mo_components_products_id = components.product_id
                    # bom_components_id = line.bom_id.bom_line_ids.filtered(lambda l : l.product_id.id == mo_components_products_id.id)
                    #
                    # if mo_components_products_id and bom_components_id and mo_components_products_id.id == bom_components_id.product_id.id:
                    #     if bom_components_id.quantity_formula:
                    #         res = re.findall(number_pattern, bom_components_id.quantity_formula)
                    #         if len(res)>=1:
                    #             new_qty = float(res[0])
                    #             components.with_context(bypass_procurement_creation=True,no_procurement=True).product_uom_qty = new_qty

                    # if bom_components_id and bom_components_id.child_bom_id:
                    #     for child_mo in line.production_id._get_children():
                    #         if child_mo.product_id.id == components.product_id.id:
                    #             child_mo.product_qty = components.product_uom_qty
                    #             self._cr.commit()

            # for line in wizard.line_ids:
            #     for components in line.production_id.move_raw_ids:
            #         mo_components_products_id = components.product_id
            #         bom_components_id = line.bom_id.bom_line_ids.filtered(lambda l : l.product_id.id == mo_components_products_id.id)
            #         if bom_components_id and bom_components_id.child_bom_id:
            #             for child_mo in line.production_id._get_children():
            #                 if child_mo.product_id.id == components.product_id.id:
            #                     update_quantity_wizard = qty_change_wizard_obj.create({
            #                         'mo_id': child_mo.id,
            #                         'product_qty': components.product_uom_qty
            #                     })
            #                     # child_mo.product_qty = components.product_uom_qty
            #                     ctx = self._context.copy()
            #                     ctx.update({'bypass_procurement_creation': True})
            #                     update_quantity_wizard.with_context(bypass_procurement_creation=True,
            #                                                         no_procurement=True).change_prod_qty()