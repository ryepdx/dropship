from openerp.osv import fields, orm

class product_product(orm.Model):
    _inherit = "product.product"
    _columns = {
        "dropship": fields.boolean('Dropship if no stock is on hand'),
    }

    def onchange_dropship(self, cr, uid, ids, dropship):
        if dropship:
            return {'value': {'procure_method': 'make_to_order', 'supply_method': 'buy'}}

        return {}

    def onchange_supply_method(self, cr, uid, ids, supply_method):
        if supply_method != "buy":
            return {'value': {'dropship': False}}

        return {}

    def onchange_procure_method(self, cr, uid, ids, procure_method):
        if procure_method != "make_to_order":
            return {'value': {'dropship': False}}

        return {}