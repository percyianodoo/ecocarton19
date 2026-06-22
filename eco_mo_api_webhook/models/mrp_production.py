from odoo import models, api, _
from odoo.exceptions import UserError
import requests
import json
import logging
import datetime

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _set_qty_producing(self, pick_manual_consumption_moves=True):
        """Skip auto-filling move lines when context flag is set."""
        if self.env.context.get('skip_auto_fill_qty'):
            return
        return super()._set_qty_producing(pick_manual_consumption_moves)

    def _set_quantities(self):
        """Skip auto-filling quantities when context flag is set."""
        if self.env.context.get('skip_auto_fill_qty'):
            return
        return super()._set_quantities()

    def _post_inventory(self, cancel_backorder=False):
        """
        Before _post_inventory posts the moves via _action_done (which needs lots),
        clear all raw material move lines so nothing tries to post with missing lots.
        After posting, the raw moves will be 'done' with 0 quantity, ready for
        mo_fg_complete to write the actual consumed quantities.
        """
        if self.env.context.get('skip_auto_fill_qty'):
            for order in self:
                # Clear all move lines on raw moves before _action_done is called
                for move in order.move_raw_ids:
                    if move.state not in ('done', 'cancel'):
                        # Unlink all move lines (auto-filled or not)
                        move.move_line_ids.sudo().unlink()
                        # Mark as picked=False so it gets cancelled, not done with bad data
                        # Then re-mark picked=True with quantity=0 so the move is done with 0 qty
                        move.sudo().write({'picked': True, 'quantity': 0})
        return super()._post_inventory(cancel_backorder=cancel_backorder)


    def action_send_nested_webhook(self):
        """Builds the nested JSON payload and sends it via POST request."""
        
        # 1. Helper Function
        def extract_mo_data(mo):
            delivery_date = (mo.date_deadline + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S') if mo.date_deadline else ""
            last_updated_date = (mo.write_date + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S') if mo.write_date else ""
            scheduled_date = (mo.date_start + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S') if mo.date_start else ""

            moves = []
            for move in mo.move_raw_ids:

                move_lines_array = []
                
                for line in move.move_line_ids:
                    move_lines_array.append({
                        "location": line.location_id.complete_name if line.location_id else False,
                        "lot_no": line.lot_id.name if line.lot_id else False,
                        "quantity": line.quantity #  line.qty_done
                    })

                moves.append({
                    "id": move.id,
                    "move_line_ids":move_lines_array,
                    "product_id": [[move.product_id.id, move.product_id.default_code]],
                    "product_uom_qty": move.product_uom_qty,
                    "quantity": move.quantity
                })

            workorders = []
            for wo in mo.workorder_ids:
                workorders.append({
                    "duration": wo.duration,
                    "duration_expected": wo.duration_expected,
                    "id": wo.id,
                    "name": wo.name,
                    "product_id": [[mo.product_id.id, mo.product_id.default_code]], 
                    "qty_remaining": wo.qty_remaining,
                    "state": wo.state,
                    "workcenter_id": [[wo.workcenter_id.id, wo.workcenter_id.display_name]]
                })

            return {
                "delivery_date": delivery_date,
                "id": mo.id,
                "last_updated_date": last_updated_date,
                "move_raw_id": moves,
                "name": mo.name,
                "origin": mo.origin or "",
                "scheduled_date": scheduled_date,
                "state": mo.state,
                "work_order_id": workorders,
                "source_location": mo.location_src_id.complete_name,
                "destination_location": mo.location_dest_id.complete_name,
            }

        # Ensure this is only run for 1 record at a time
        self.ensure_one()

        # 2. Loop through the records (in case the server action triggers on multiple MOs)
        for parent_mo in self:
            payload = extract_mo_data(parent_mo)
            
            # --- Add label_info to parent MO only ---
            label_info = False
            try:
                sale_orders = parent_mo.move_dest_ids.group_id.sale_id
                if sale_orders:
                    mo_calc = sale_orders[0].mo_calc_ids
                    if mo_calc:
                        calc = mo_calc[0]
                        label_info = {
                            "width_mm":     calc.x_studio_roll_width_mm       if calc.x_studio_roll_width_mm       else False,
                            "length_mm":    calc.x_studio_length               if calc.x_studio_length               else False,
                            "thickness_mm": calc.x_studio_thickness            if calc.x_studio_thickness            else False,
                            "num_up":       calc.x_studio_pcs_cut_per_sheet    if calc.x_studio_pcs_cut_per_sheet    else False,
                        }
            except Exception:
                label_info = False
            payload["label_info"] = label_info

            # 3. Find and sort Child MOs
            payload["child_mo"] = []
            child_mos = self.env['mrp.production'].search(
                [('name', '=like', parent_mo.name + '-%')],
                order='name asc'
            )

            for child in child_mos:
                payload["child_mo"].append(extract_mo_data(child))

            # 4. Send the POST Request
            url = "http://103.76.88.37/arc.flow.UAT/workflows/custom/incoming-manufacturing-order"
            headers = {"Content-Type": "application/json"}


            # url = "http://103.76.88.39:8069/api/v2/custom/test"

            try:

                if parent_mo.x_studio_sent_to_mes:
                    raise UserError(_("Already sent to MES."))

                else:
                    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)

                    # Check if it was successful (200 or 201)
                    if response.status_code == 200:
                        parent_mo.x_studio_sent_to_mes = True
                    else:
                        raise UserError(_("API Response:\n%s") % response.text)

            except Exception as e:
                # Log the exact error to your server logs
                # _logger.error("API Connection Error for MO %s: %s", parent_mo.name, str(e))

                # Optional: Uncomment the line below if you want the user to see a popup when it fails
                # raise UserError(_("Failed to send data to external API: %s") % str(e))

                # Format the payload so it looks nice in the Odoo error popup
                pretty_payload = json.dumps(payload, indent=4)
                
                # Show the error AND the payload to the user
                # raise UserError(_("Failed to send data to external API:\n%s\n\n--- PAYLOAD DATA ---\n%s") % (str(e), pretty_payload))
                raise UserError(_("%s") % (str(e)))