from openerp.osv import fields, orm

class purchase_order_line(orm.Model):
    _inherit = "purchase.order.line"
    _columns = {
        'sale_order_line_id': fields.many2one('sale.order.line', 'Sale Order Line')
    }

purchase_order_line()

class purchase_order(orm.Model):
    _inherit = "purchase.order"
    _columns = {
        'sale_id': fields.many2one('sale.order', 'Related Sale Order'),
    }

    def action_picking_create(self, cr, uid, ids, context=None):
        res = super(purchase_order, self).action_picking_create(cr, uid, ids, context=context)
        import pdb; pdb.set_trace()
        picking_pool = self.pool.get('stock.picking')

        for purchase in self.browse(cr, uid, ids, context=context):
            if res and any([line.product_id.dropship for line in purchase.sale_id.order_line]):
                if purchase.sale_id and purchase.sale_id.order_policy == 'picking':
                    invoice_control = '2binvoiced'
                else:
                    invoice_control = 'none'

                picking_pool.write(cr, uid, res, {
                    'type': 'out',
                    'invoice_state': invoice_control,
                    'sale_id': purchase.sale_id and purchase.sale_id.id
                }, context=context)

        return res

    def _key_fields_for_grouping(self):
        """Do not merge orders that have different destination addresses."""
        field_list = super(purchase_order, self)._key_fields_for_grouping()
        return field_list + ('dest_address_id', )

    def _initial_merged_order_data(self, order):
        """Populate the destination address in the merged order."""
        res = super(purchase_order, self)._initial_merged_order_data(order)
        res['dest_address_id'] = order.dest_address_id.id
        return res

purchase_order()