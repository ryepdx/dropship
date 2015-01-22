from openerp.osv import orm, fields
from openerp.tools.translate import _
import netsvc


class sale_order_line(orm.Model):
    _inherit = "sale.order.line"
    _columns = {
        'dropship': fields.boolean('Force Dropshipping')
    }

sale_order_line()


class sale_order(orm.Model):
    _inherit = "sale.order"

    def _prepare_order_line_procurement(self, cr, uid, order, line, move_id, date_planned, context=None):
        res = super(sale_order, self)._prepare_order_line_procurement(
            cr, uid, order, line, move_id, date_planned, context
        )
        res['sale_order_line_id'] = line.id

        if line.product_id.dropship:
            res['location_id'] = order.partner_id.property_stock_supplier.id

        return res

    def _create_dropship_procurements(self, cr, uid, order, order_lines, context=None):
        wf_service = netsvc.LocalService("workflow")
        proc_obj = self.pool.get('procurement.order')

        for line in order_lines:
            date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)
            proc_id = proc_obj.create(cr, uid, self._prepare_order_line_procurement(
                cr, uid, order, line, False, date_planned, context=context), context=context)

            line.write({'procurement_id': proc_id})
            wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)

    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        normal_lines = []
        dropship_lines = []

        for line in order_lines:
            if line.type == 'make_to_order' and line.product_id.dropship:
                dropship_lines.append(line)
            else:
                normal_lines.append(line)

        self._create_dropship_procurements(cr, uid, order, dropship_lines, context=context)

        return super(sale_order, self)._create_pickings_and_procurements(
            cr, uid, order, normal_lines, picking_id, context)

    def action_button_confirm(self, cr, uid, ids, context=None):
        for sale in self.browse(cr, uid, ids, context=context):
            for line in sale.order_line:
                if line.type == 'make_to_order' and line.product_id.dropship and not line.product_id.seller_ids:
                    raise orm.except_orm(
                        _('Warning!'), _('Product has no suppliers: "%s" (code: %s)') % (
                            line.product_id.name, line.product_id.default_code))

        return super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)

sale_order()

class procurement_order(orm.Model):
    _inherit = 'procurement.order'
    _columns = {
        'sale_order_line_id': fields.many2one('sale.order.line', 'Sale Order Line'),
    }

    def create_procurement_purchase_order(self, cr, uid, procurement, po_vals, line_vals, context=None):
        if procurement.sale_order_line_id:
            sale_order = procurement.sale_order_line_id.order_id
            sale_order_line = procurement.sale_order_line_id
            product = sale_order_line.product_id

            po_vals['sale_id'] = sale_order.id

            if (product.dropship and product.qty_available == 0) or sale_order_line.dropship:
                po_vals['location_id'] = sale_order.partner_id.property_stock_customer.id
                po_vals['dest_address_id'] = sale_order.partner_shipping_id.id
                po_vals['invoice_method'] = 'order'

            if procurement.sale_order_line_id:
                line_vals['sale_order_line_id'] = procurement.sale_order_line_id.id
            else:
                line_vals['sale_order_line_id'] = False

        return super(procurement_order, self).create_procurement_purchase_order(
            cr, uid, procurement, po_vals, line_vals, context
        )

procurement_order()