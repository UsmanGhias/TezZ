
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MassActionDetails(models.TransientModel):
    _name = "mass.action.details"
    _description = "Show Stats Details after mass confirm "

    @api.model
    def _get_record(self):
        result = self.env['sale.order.line'].browse(
            self._context['active_ids'])
        return result.ids

    sale_order_line_ids = fields.Many2many(
        "sale.order.line", string="Sale order line", default=_get_record)
    
    def confirm_all(self):
        success_order_line = self.sale_order_line_ids.filtered(lambda so : so.marketplace_state == 'pending')
        success_order_line.action_mass_approve()
        msg = "<p style='font-size: 15px'>Total number of orders approved: <strong>" + str(len(success_order_line)) + "</strong></p>"
        return self.env["mp.wizard.message"].generated_message(msg, "Confirm Status")
