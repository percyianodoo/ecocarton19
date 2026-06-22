from odoo import models, _, api, fields
from odoo.exceptions import UserError

class MoCalculation(models.Model):
    _name = 'mo.calculation'

    x_studio_raw_material = fields.Many2one("product.template", string="Raw Material", store=True, copy=True, ondelete="set null")
    x_studio_batch = fields.Many2one("stock.lot", string="Batch", store=True, copy=True, ondelete="set null")
    x_studio_roll_kg = fields.Float(string="Paper Roll (KG)", store=True, copy=True)
    x_studio_gsm = fields.Float(string="GSM", related="x_studio_raw_material.x_studio_gsm", readonly=True)
    x_studio_pe = fields.Float(string="PE", related="x_studio_raw_material.x_studio_pe", readonly=True)
    x_studio_roll_width_mm = fields.Float(string="Roll Width (mm)", related="x_studio_raw_material.x_studio_roll_width_mm", store=True , readonly=True)
    x_studio_no_of_cups = fields.Float(string="AO issue QTY", copy=True, store=True)
    x_studio_die_board_up = fields.Float(string="Die Board Up",related="x_studio_pcs_cut_per_sheet", store=True, readonly=True)
    x_studio_no_of_sheets = fields.Float(string="Minimum good sheet needed", compute='_compute_no_of_sheets', store=True, readonly=True)
    x_studio_wastage_formula = fields.Char(string="Wastage Formula", copy=True, store=True)
    x_studio_test_paper_1 = fields.Float(string="Test Paper", copy=True, store=True)

    x_studio_wastage_calculation = fields.Float(string="Printing job total sheet needed", compute='_compute_wastage_calculation', store=True, readonly=True)

    x_studio_plain_job = fields.Float(string="Generic job total sheet needed", compute='_compute_plain_job', store=True, readonly=True)

    x_studio_formula_of_kg_used_per_total_no_of_sheets_1 = fields.Char(string="Formula Of Kg Used Per Total No Of Sheets 1", copy=True, store=True)

    x_studio_kg_for_total_no_of_sheets = fields.Float(string="Total KG needed", compute='_compute_kg_for_total_no_of_sheets', store=True, readonly=True)

    x_studio_paper_roll_length_formula = fields.Char(string="Paper Roll Length Formula", copy=True, store=True)

    x_studio_1_paper_roll_length_meterl = fields.Float(string="1) Paper Roll Length meter(L)", compute='_compute_paper_roll_length_meter', store=True, readonly=True)

    x_studio_roll_to_sheet_formula = fields.Char(string="Roll To Sheet Formula", copy=True, store=True)

    x_studio_length = fields.Float(string="'Paper cut size (mm)", store=True, copy=True)

    x_studio_2_sheets = fields.Float(string="2) Sheets", compute='_compute_x_studio_sheets', store=True, readonly=True)

    x_studio_3_wastage = fields.Char(string="3) Wastage", copy=True, store=True)

    x_studio_test_paper = fields.Float(string="Test Paper", store=True, copy=True)

    x_studio_wastage = fields.Float(string="Minimum good sheet needed", compute='_compute_x_studio_wastage', store=True, readonly=True)

    x_studio_pcs_cut_per_sheet = fields.Float(string="Number of up", store=True, copy=True)

    x_studio_sheet_convert_to_pcs = fields.Float(string="Sheet Convert to pcs", compute='_compute_x_studio_sheet_convert_to_pcs', store=True, readonly=True)

    product_id = fields.Many2one(
        'product.product',
        string="Product (from sale line)",
        related='sale_line_id.product_id',
        store=False,
        readonly=True,
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string="Product Template (from sale line)",
        related='sale_line_id.product_id.product_tmpl_id',
        store=False,
        readonly=True,
    )
    sale_id = fields.Many2one("sale.order", string="Sale Order", ondelete="cascade")
    sale_line_id = fields.Many2one("sale.order.line", string="Sale Order Line", ondelete="cascade")

    is_mo_created = fields.Boolean(string="Is Mo Created?")
    production_id = fields.Many2one("mrp.production", string="Manufacturing Order")
    bom_id = fields.Many2one(
        'mrp.bom',
        string="Bill of Material",
        domain="[('type','=', 'normal'), '|', ('product_id','=', product_id), ('product_tmpl_id','=', product_tmpl_id)]",
    )

    @api.onchange('bom_id')
    def onchange_bom_ids_method(self):
        if self.bom_id:
            self.x_studio_pcs_cut_per_sheet = self.bom_id.pcs_cut_per_sheet
            self.x_studio_length = self.bom_id.length

    def action_generate_mo(self):
        context = self.env.context.copy()
        context.update({'selected_so_line_id': self.sale_line_id.id})
        context.update({'bom_id': self.bom_id.id})
        self.env.context = context
        # self.sale_line_id.state = 'draft'
        self.sale_id.state = 'draft'
        before_mos = self.sale_id.mrp_production_ids

        self.sale_id.action_confirm()
        self.is_mo_created = True

        after_mos = self.sale_id.mrp_production_ids

        is_remaining_mo_generation = self.search([('sale_id','=',self.sale_id.id),('is_mo_created','=',False)],limit=1)
        if is_remaining_mo_generation:
            self.sale_id.state = 'draft'
            self.sale_id.locked = False

        #
        new_mos = (after_mos - before_mos).sorted(key=lambda mo: mo.id,reverse = True)

        # in newmos data lok like==> currentlys -7,-6,-5.....1
        for count, mo in enumerate(new_mos,start=1):
            if len(mo.name.split('-'))==2:
                mo.name =mo.name.split('-')[0] + '--'+str(count)
        self._cr.commit()
        for count, mo in enumerate(new_mos,start=1):
            if len(mo.name.split('--'))==2:
                mo.name =mo.name.split('-')[0] + '-'+str(count)
        self._cr.commit()
        wizard = self.env['mo.calculation.wizard'].create({
            'calc_id': self.id,
            'line_ids': [(0, 0, {
                'production_id': mo.id,
            }) for mo in new_mos]
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'MO Calculation',
            'res_model': 'mo.calculation.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }

    def action_open_wizard(self):
        """Open the wizard again with existing lines"""
        self.ensure_one()

        # Check if a wizard already exists for this calc_id
        wizard = self.env['mo.calculation.wizard'].search([('calc_id', '=', self.id)], limit=1)

        if not wizard:
            # If no wizard exists yet, create one fresh with MOs
            wizard = self.env['mo.calculation.wizard'].create({
                'calc_id': self.id,
                'line_ids': [(0, 0, {
                    'production_id': mo.id,
                }) for mo in self.production_id]
            })

        return {
            'type': 'ir.actions.act_window',
            'name': 'MO Calculation',
            'res_model': 'mo.calculation.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }

    @api.depends('x_studio_pcs_cut_per_sheet','x_studio_wastage')
    def _compute_x_studio_sheet_convert_to_pcs(self):
        for record in self:
            # Ensure divisor is not zero
            if record.x_studio_pcs_cut_per_sheet != 0 and record.x_studio_wastage != 0:
                record['x_studio_sheet_convert_to_pcs'] = record.x_studio_wastage * record.x_studio_pcs_cut_per_sheet



    @api.depends('x_studio_2_sheets','x_studio_test_paper')
    def _compute_x_studio_wastage(self):
        for record in self:
            # Ensure divisor is not zero
            if record.x_studio_2_sheets != 0:
                record['x_studio_wastage'] = (record.x_studio_2_sheets - record.x_studio_test_paper) * 0.97



    @api.depends('x_studio_1_paper_roll_length_meterl','x_studio_length')
    def _compute_x_studio_sheets(self):
        for record in self:
            # Ensure divisor is not zero
            if record.x_studio_1_paper_roll_length_meterl != 0 and record.x_studio_length != 0:
                record['x_studio_2_sheets'] = record.x_studio_1_paper_roll_length_meterl / (record.x_studio_length / 1000)



    @api.depends('x_studio_roll_kg','x_studio_gsm','x_studio_pe','x_studio_roll_width_mm')
    def _compute_paper_roll_length_meter(self):
        for record in self:
            # Ensure divisor is not zero
            if record.x_studio_gsm + record.x_studio_pe != 0 and record.x_studio_roll_width_mm != 0:
                record['x_studio_1_paper_roll_length_meterl'] = (
                        record.x_studio_roll_kg * 1000 / (record.x_studio_gsm + record.x_studio_pe) / (
                            record.x_studio_roll_width_mm / 1000)
                )
            else:
                # Set to 0 or handle error case if divisor is zero
                record['x_studio_1_paper_roll_length_meterl'] = 0


    @api.depends('x_studio_length','x_studio_no_of_sheets','x_studio_roll_width_mm','x_studio_gsm','x_studio_pe','x_studio_wastage_calculation')
    def _compute_kg_for_total_no_of_sheets(self):
        for record in self:
            # Ensure divisor is not zero
            if record.x_studio_no_of_sheets != 0 and record.x_studio_length != 0 and record.x_studio_roll_width_mm != 0:
                record['x_studio_kg_for_total_no_of_sheets'] = (record.x_studio_wastage_calculation * (
                            record.x_studio_length / 1000)) * (record.x_studio_roll_width_mm / 1000) * ((record.x_studio_gsm + record.x_studio_pe) / 1000)


    @api.depends('x_studio_no_of_sheets')
    def _compute_plain_job(self):
        for record in self:
            # Ensure divisor is not zero
            if record.x_studio_no_of_sheets != 0:
                record['x_studio_plain_job'] = (record.x_studio_no_of_sheets) * 1.03


    @api.depends('x_studio_no_of_cups','x_studio_die_board_up')
    def _compute_no_of_sheets(self):
        for record in self:
            # Ensure divisor is not zero
            if record.x_studio_die_board_up != 0 and record.x_studio_no_of_cups != 0:
                record['x_studio_no_of_sheets'] = record.x_studio_no_of_cups / record.x_studio_die_board_up

    @api.depends('x_studio_no_of_sheets','x_studio_test_paper')
    def _compute_wastage_calculation(self):
        for record in self:
            # Ensure divisor is not zero
            if record.x_studio_no_of_sheets != 0:
                record['x_studio_wastage_calculation'] = (record.x_studio_no_of_sheets * 1.03) + (record.x_studio_test_paper)


