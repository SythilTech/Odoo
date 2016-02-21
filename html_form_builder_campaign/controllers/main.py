import openerp.http as http
import openerp
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import base64
import json

class html_field_response():
     error = ""
     return_data = ""
     history_data = ""

class HtmlFormControllerCampaign(openerp.addons.html_form_builder.controllers.main.HtmlFormController):

    @http.route('/form/campaign',type="http", auth="public", csrf=False)
    def my_insert(self, **kwargs):
        
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        #the referral string is what the campaign looks for
        secure_values = {}
        history_values = {}
        form_error = False
        ref_url = http.request.httprequest.headers['Referer']
        entity_form = http.request.env['html.form'].sudo().browse(int(values['form_id']))
        new_history = http.request.env['html.form.history'].sudo().create({'ref_url':ref_url, 'html_id': entity_form.id})
        
        #populate an array which has ONLY the fields that are in the form (prevent injection)
        for fi in entity_form.fields_ids:
            
            method = '_process_html_%s' % (fi.field_type.html_type,)
	    action = getattr(self, method, None)
	        
	    if not action:
		raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
	
            field_valid = html_field_response()
	    field_valid = action(fi, values[fi.html_name])
	    
	    if field_valid.error == "":
	        form_error = False
	        secure_values[fi.field_id.name] = field_valid.return_data
                new_history.insert_data.sudo().create({'html_id': new_history.id, 'field_id':fi.field_id.id, 'insert_value':field_valid.history_data})
            else:
                form_error = True

        if form_error:
            #redirect back to the page
            return werkzeug.utils.redirect(ref_url)
        else:
            #default values
            for df in entity_form.defaults_values:
                secure_values[df.field_id.name] = df.default_value
                new_history.insert_data.sudo().create({'html_id': new_history.id, 'field_id':df.field_id.id, 'insert_value':df.default_value})
        
            new_record = http.request.env[entity_form.model_id.model].sudo().create(secure_values)
            new_history.record_id = entity_form.id
        
            #Add the new partner to a campaign
            for act in entity_form.campaign_id.activity_ids:
                if act.start:
                    wi = request.env['marketing.campaign.workitem'].create({'campaign_id': entity_form.campaign_id.id, 'activity_id': act.id, 'partner_id': new_record.id, 'res_id': new_record.id})
                    wi.process()
            
            return werkzeug.utils.redirect(entity_form.return_url)