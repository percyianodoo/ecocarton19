from odoo import models, api, fields, _
from odoo.exceptions import UserError
import requests
import json
import logging
import datetime

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_send_picking_webhook(self):
        """Builds a flat JSON payload for a completed stock.picking and POSTs it."""

        self.ensure_one()

        def extract_picking_data(picking):

            done_dt = picking.date_done or fields.Datetime.now()
            date_done = (done_dt + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
           
            # Single product line and single lot per transfer.
            move = picking.move_ids_without_package[:1]
            line = move.move_line_ids[:1] if move else move  # lot lives on the move line

            quant = False
            if line and line.lot_id and move and picking.location_dest_id:
                quant = self.env['stock.quant'].search([
                    ('lot_id', '=', line.lot_id.id),
                    ('product_id', '=', move.product_id.id),
                    ('location_id', '=', line.location_dest_id.id),
                ], limit=1)

            return {
                # "name": picking.name,
                "date_done": date_done,
                # "origin": picking.origin or "",
                # "state": picking.state,
                "item_code": move.product_id.default_code if move else False,
                "quantity": move.quantity if move else 0,
                "lot_no": line.lot_id.name if line and line.lot_id else False,
                "id": quant.id if quant else False,
                # "source_location": picking.location_id.complete_name if picking.location_id else False,
                "transferred_location": picking.location_dest_id.complete_name if picking.location_dest_id else False,
                "uom": move.product_uom.name if move else False,
            }

        for picking in self:
            payload = extract_picking_data(picking)

            # url = "http://103.76.88.37/arc.flow.UAT/workflows/custom/incoming-stock-picking"
            headers = {"Content-Type": "application/json"}

            url = "http://103.76.88.39:8069/api/v2/custom/test"

            try:

                response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)

                # Check if it was successful (200 or 201)
                if response.status_code != 200:
                    raise UserError(_("API Response:\n%s") % response.text)
                    

            except Exception as e:
                pretty_payload = json.dumps(payload, indent=4)

                # raise UserError(_("Failed to send data to external API:\n%s\n\n--- PAYLOAD DATA ---\n%s") % (str(e), pretty_payload))
                raise UserError(_("%s") % (str(e)))