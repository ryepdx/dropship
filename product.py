from openerp.osv import fields, orm

class product_product(orm.Model):

    _inherit = "product.product"
    _columns = {
        "dropship": fields.boolean('Dropship if no stock is on hand'),
    }