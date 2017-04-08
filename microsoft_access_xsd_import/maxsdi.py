from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
from lxml import etree
import base64


class html_gen_tran(models.TransientModel):

    _name = "maxsdi.wizard"
    
    my_model = fields.Many2one('ir.model', required='True', string='Select Model')
    load_file = fields.Binary(required='True', string='XSD File')
    filename = fields.Char('Filename')

    @api.one
    def read_xsd(self):
        if self.my_model.id > 0:
            file_contents = base64.b64decode(self.load_file)
           
            my_id = self.id
            root = etree.fromstring(file_contents)
            
            my_element_counter = 0
            
            my_elements = root.xpath('//xsd:element',namespaces={'xsd': 'http://www.w3.org/2001/XMLSchema','od':'urn:schemas-microsoft-com:officedata'})
            
            
	    my_max = self.env['maxsdi'].create({'my_model':self.my_model.id, 'load_file':self.load_file})
                    
            for child in my_elements:
                if my_element_counter >= 3:
                    attributes = child.attrib
                    
                    access_type = attributes["{urn:schemas-microsoft-com:officedata}jetType"]
                    
            
                    my_type = ""
                    if access_type == "longinteger":
                        my_type = "integer"
                    elif access_type == "yesno":
                        my_type = "boolean"
                    elif access_type == "text":
                        my_type = "char"
                    elif access_type == "single":
                        my_type = "float"
                    elif access_type == "datetime":
                        my_type = "datetime"
                    elif access_type == "memo":
                        my_type = "text"
                    elif access_type == "byte":
                        my_type = "integer"
                    elif access_type == "integer":
                        my_type = "integer"
                    elif access_type == "autonumber":
                        my_type = "integer"
                    else:
                        _logger.error("unknown type:" + str(access_type))
                    
                    _logger.error(self.id)
                    
                    
                    
                    self.env["maxsdi.field"].create({'maxsdi_id':my_max.id,'name': attributes["name"], 'ttype':my_type})
                    
                my_element_counter += 1
    

    
class html_gen_tran(models.Model):

    _name = "maxsdi"
    
    my_model = fields.Many2one('ir.model', string='Select Model')
    load_file = fields.Binary(string='XSD File')
    filename = fields.Char('Filename')
    field_ids = fields.One2many('maxsdi.field','maxsdi_id', string='Import Fields')

    @api.one
    def add_fields(self):
        for fi in self.field_ids:
            self.env["ir.model.fields"].create({'name': fi.name, 'ttype':fi.ttype,'model_id':self.my_model.id})
        
class temp_field(models.Model):

    _name = "maxsdi.field"
    
    maxsdi_id = fields.Many2one('maxsdi')
    name = fields.Char('Field Name')
    ttype = fields.Char('Field Type')
    
    