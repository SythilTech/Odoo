from openerp import models, fields, api
import logging
from tempfile import TemporaryFile, NamedTemporaryFile
import zipfile
import base64
_logger = logging.getLogger(__name__)
from StringIO import StringIO
import os

class CrmMigrateImageWizard(models.TransientModel):

    _name = "crm.migrate.image.wizard"

    zip_path = fields.Char(string='Zip File Path', default="/odoo/import/import.zip")
    map_field = fields.Many2one('ir.model.fields', domain="[('model_id.model','=','res.partner'),('ttype','=','integer')]", string='Mapping Field')
    
    @api.one
    def import_images(self):
        
        import_object = self.env['crm.migrate.image'].create({'map_field':self.map_field.id})

        myzipfile = zipfile.ZipFile(self.zip_path)
        for name in myzipfile.namelist():
            zippy = myzipfile.open(name)
            image_string = zippy.read()
            
            #only proceed if the filename can be parsed into the type of the map_field
            try:
                my_id = int(os.path.splitext(name)[0])
            except:
                self.env['import.image.history'].create({'migrate_image_id':import_object['id'],'filename':name,'state':'Failure','note':'Type mismatch'})
                continue
            
	    my_partner = self.env['res.partner'].search([[self.map_field.name,'=',os.path.splitext(name)[0]]])
	        
	    if len(my_partner) == 1:
		my_partner.image = base64.b64encode(image_string)
	        self.env['import.image.history'].create({'migrate_image_id':import_object['id'],'filename':name,'state':'Success'})
	    elif len(my_partner) > 1:
		#more then one Partner with identifer
		self.env['import.image.history'].create({'migrate_image_id':import_object['id'],'filename':name,'state':'Failure','note':'More then one record with this id'})
	    else:
		#customer does not exist
                self.env['import.image.history'].create({'migrate_image_id':import_object['id'],'filename':name,'state':'Failure','note':'No record with this id'})
    
class CrmMigrateImage(models.Model):

    _name = "crm.migrate.image"

    map_field = fields.Many2one('ir.model.fields', domain="[('model_id.model','=','res.partner')]", string='Mapping Field', readonly='True')
    filename = fields.Char(string="Filename")
    import_history = fields.One2many('import.image.history','migrate_image_id', string="Imported Images");
    
    
class ImportImageHistory(models.Model):

    _name = "import.image.history"
    _order = "state asc"

    migrate_image_id = fields.Many2one('crm.migrate.image', string="Migrate ID")
    filename = fields.Char(string="Filename")
    state = fields.Char(string="State")
    note = fields.Text(string="Note")