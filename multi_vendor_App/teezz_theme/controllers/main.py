from odoo import http
from odoo.http import request


class TeZzController(http.Controller):

    @http.route('/teezz/cart/count', type='json', auth='public', website=True)
    def cart_count(self):
        order = request.website.sale_get_order()
        count = sum(line.product_uom_qty for line in order.order_line) if order else 0
        return {'count': int(count)}
