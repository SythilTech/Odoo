import openerp.http as http
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import base64

class MyController(http.Controller):

    @http.route('/form/thankyou', type="http", auth="public", website=True)
    def ehtml_thanks(self, **kw):
        return http.request.render('entity_html_form.ehtml_thank_you', {})
        
    @http.route('/form/myinsert',type="http", auth="public")
    def my_insert(self, **kwargs):
        
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        #the referral string is what the campaign looks for
        secure_values = {}
        history_values = {}
        
        ref_url = http.request.httprequest.headers['Referer']
        
        entity_form = http.request.env['ehtml.formgen'].sudo().browse(int(values['form_id']))
        
        new_history = http.request.env['ehtml.history'].sudo().create({'ref_url':ref_url, 'html_id': entity_form.id})
        
        #populate an array which has ONLY the fields that are in the form (prevent injection)
        for fi in entity_form.fields_ids:
            if fi.field_id.ttype == "binary":
                secure_values[fi.field_id.name] = base64.encodestring(values[fi.html_name].read() )    
            else:
                secure_values[fi.field_id.name] = values[fi.html_name]
            new_history.insert_data.sudo().create({'html_id': new_history.id, 'field_id':fi.field_id.id, 'insert_value':values[fi.html_name]})

        #default values
        for df in entity_form.defaults_values:
            secure_values[df.field_id.name] = df.default_value
            new_history.insert_data.sudo().create({'html_id': new_history.id, 'field_id':df.field_id.id, 'insert_value':df.default_value})
        
        new_record = http.request.env[entity_form.model_id.model].sudo().create(secure_values)
        new_history.record_id = entity_form.id
        
        return werkzeug.utils.redirect(entity_form.return_url)