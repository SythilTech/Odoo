import openerp.http as http
import requests
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

class HtmlFormController(http.Controller):

    @http.route('/form/thankyou', type="http", auth="public", website=True)
    def html_thanks(self, **kw):
        return http.request.render('html_form_builder.html_thank_you', {})
                
    @http.route('/form/insert',type="http", auth="public", csrf=False)
    def my_insert(self, **kwargs):
        
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        entity_form = http.request.env['html.form'].sudo().browse(int(values['form_id']))
        
        ref_url = ""
        if 'Referer' in http.request.httprequest.headers:
            ref_url = http.request.httprequest.headers['Referer']
                       
        #Captcha Check
        if entity_form.captcha:
               
            #Redirect them back if they didn't answer the captcha
            if 'g-recaptcha-response' not in values:
                return werkzeug.utils.redirect(ref_url)         
            
            payload = {'secret': str(entity_form.captcha_secret_key), 'response': str(values['g-recaptcha-response'])}
	    response_json = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)
                        
            if response_json.json()['success'] != True:
                return werkzeug.utils.redirect(ref_url)
        
        #the referral string is what the campaign looks for
        secure_values = {}
        history_values = {}
        form_error = False
        new_history = http.request.env['html.form.history'].sudo().create({'ref_url':ref_url, 'html_id': entity_form.id})
        
        #populate an array which has ONLY the fields that are in the form (prevent injection)
        for fi in entity_form.fields_ids:
            if fi.html_name in values:
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
 
 
            #Execute all the server actions
            for sa in entity_form.submit_action:
             
                method = '_html_action_%s' % (sa.setting_name,)
 	        action = getattr(self, method, None)
 	        
 	        if not action:
 		    raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
 	
 	        #Call the submit action, passing the action settings and the history object
                action(sa, new_history)
 
            return werkzeug.utils.redirect(entity_form.return_url)
        
    def _process_html_textbox(self, field, field_data):
        """Validation for textbox and preps for insertion into database"""
        html_response = html_field_response()
        html_response.error = ""
        html_response.return_data = field_data
        html_response.history_data = field_data

        return html_response

    def _process_html_checkbox_boolean(self, field, field_data):
        """Validation for Checkboxes(Boolean) and preps for insertion into database"""
        html_response = html_field_response()
        html_response.error = ""
        html_response.return_data = field_data
        html_response.history_data = field_data

        return html_response
        
    def _process_html_dropbox_m2o(self, field, field_data):
        """Validation for Dropbox(m2o) and preps for insertion into database"""
        html_response = html_field_response()
        html_response.error = ""
        html_response.return_data = field_data
        html_response.history_data = field_data

        return html_response
        
    def _process_html_textarea(self, field, field_data):
        html_response = html_field_response()
        html_response.error = ""
        html_response.return_data = field_data
        html_response.history_data = field_data

        return html_response

    def _process_html_radio_group_selection(self, field, field_data):
        html_response = html_field_response()
        html_response.error = ""
        html_response.return_data = field_data
        html_response.history_data = field_data

        return html_response
    
    def _process_html_dropbox(self, field, field_data):
        """Validation for dropbox and preps for insertion into database"""
        html_response = html_field_response()
        html_response.error = ""

        if field.field_id.ttype == "selection":
    
            #ensure that the user isn't trying to inject data that is not in the selection
    	    selection_list = dict(request.env[field.field_id.model_id.model]._columns[field.field_id.name].selection)
    	        
    	    for selection_value,selection_label in selection_list.items():
    	        if field_data == selection_value:
    	            html_response.error = ""
		    html_response.return_data = field_data
		    html_response.history_data = field_data
		    
    	            return html_response
    	        
            html_response.error = "This is not a valid selection"
	    html_response.return_data = ""
	    html_response.history_data = ""
		
            return html_response
            