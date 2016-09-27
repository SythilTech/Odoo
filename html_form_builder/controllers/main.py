import openerp.http as http
import requests
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)
import openerp
import werkzeug
import base64
import json
import sys
from urlparse import urlparse

from openerp.exceptions import ValidationError

class html_field_response():
     error = ""
     return_data = ""
     history_data = ""

class HtmlFormController(http.Controller):

    def _html_action_custom_server_action(self, submit_action, history_data):
        form_record = request.env[history_data.html_id.model_id.model].browse(history_data.record_id)
        request.session.model('ir.actions.server').run(submit_action.custom_server_action.id, {'active_id': form_record.id, 'active_model':history_data.html_id.model_id.model} )
        
    @http.route('/form/thankyou', type="http", auth="public", website=True)
    def html_thanks(self, **kw):
        return http.request.render('html_form_builder.html_thank_you', {})

    @http.route('/form/sinsert',type="http", auth="public", csrf=False)
    def my_secure_insert(self, **kwargs):
        
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        if values['my_pie'] != "3.14":
            return "You touched my pie!!!"

        #Check if this form still exists
        if http.request.env['html.form'].sudo().search_count([('id','=',int(values['form_id']) )]) == 0:
            return "The form no longer exists"

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
        
        secure_values = {}
        history_values = {}
        return_errors = []
        insert_data_dict = []
        form_error = False
        
        #populate an array which has ONLY the fields that are in the form (prevent injection)
        for fi in entity_form.fields_ids:
            #Required field check
            if fi.setting_general_required and fi.html_name not in values:
                return_item = {"html_name": fi.html_name,"error_messsage": "This field is required"}
                return_errors.append(return_item)
                form_error = True
        
            if fi.html_name in values:
                method = '_process_html_%s' % (fi.field_type.html_type,)
	        action = getattr(self, method, None)
	        
	        if not action:
		    raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
	
                field_valid = html_field_response()
                
	        field_valid = action(fi, values[fi.html_name])

	        if field_valid.error == "":
	            secure_values[fi.field_id.name] = field_valid.return_data
                    insert_data_dict.append({'field_id':fi.field_id.id, 'insert_value':field_valid.history_data})
                else:
                    return_item = {"html_name": fi.html_name,"error_messsage": field_valid.error}
                    return_errors.append(return_item)
                    form_error = True
                    
        if form_error:
            return json.JSONEncoder().encode({'status': 'error', 'errors':return_errors})
        else:
            new_history = http.request.env['html.form.history'].sudo().create({'ref_url':ref_url, 'html_id': entity_form.id})
            
            for insert_field in insert_data_dict:
                 new_history.insert_data.sudo().create({'html_id': new_history.id, 'field_id': insert_field['field_id'], 'insert_value': insert_field['insert_value'] })
            
            #default values
            for df in entity_form.defaults_values:
                if df.field_id.ttype == "many2many":
                    secure_values[df.field_id.name] = [(4, request.env[df.field_id.relation].search([('name','=',df.default_value)])[0].id )]
                else:
                    secure_values[df.field_id.name] = df.default_value
                
                new_history.insert_data.sudo().create({'html_id': new_history.id, 'field_id':df.field_id.id, 'insert_value':df.default_value})
        
            try:
                new_record = http.request.env[entity_form.model_id.model].sudo().create(secure_values)
            except Exception as e:
                return "Failed to insert record<br/>\n" + str(e)
                
            new_history.record_id = new_record.id
 
 
            #Execute all the server actions
            for sa in entity_form.submit_action:
             
                method = '_html_action_%s' % (sa.setting_name,)
 	        action = getattr(self, method, None)
 	        
 	        if not action:
 		    raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
 	
 	        #Call the submit action, passing the action settings and the history object
                action(sa, new_history)
 
            if 'is_ajax_post' in values:
                return json.JSONEncoder().encode({'status': 'success', 'redirect_url':entity_form.return_url})
            else:
                return werkzeug.utils.redirect(entity_form.return_url)
                
    @http.route('/form/insert',type="http", auth="public", csrf=False)
    def my_insert(self, **kwargs):
        
        values = {}
	for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        #Check if this form still exists
        if http.request.env['html.form'].sudo().search_count([('id','=',int(values['form_id']) )]) == 0:
            return "The form no longer exists"

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
                if df.field_id.ttype == "many2many":
                    secure_values[df.field_id.name] = [(4, request.env[df.field_id.relation].search([('name','=',df.default_value)])[0].id )]
                else:
                    secure_values[df.field_id.name] = df.default_value
                
                new_history.insert_data.sudo().create({'html_id': new_history.id, 'field_id':df.field_id.id, 'insert_value':df.default_value})
                     
            try:
                new_record = http.request.env[entity_form.model_id.model].sudo().create(secure_values)
            except Exception as e:
                return "Failed to insert record<br/>\n" + str(e)
                
            new_history.record_id = new_record.id 
 
            #Execute all the server actions
            for sa in entity_form.submit_action:
             
                method = '_html_action_%s' % (sa.setting_name,)
 	        action = getattr(self, method, None)
 	        
 	        if not action:
 		    raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
 	
 	        #Call the submit action, passing the action settings and the history object
                action(sa, new_history)
 
            return werkzeug.utils.redirect(entity_form.return_url)

    def _process_html_input_group(self, field, field_data):
        """Validation for input_groups and preps for insertion into database"""
        html_response = html_field_response()
        html_response.error = ""
                        
        input_group_obj = json.loads(field_data)
        all_inserts = []
        for row in input_group_obj:
            create_list = []
            
            #Only allow fields in the sub field list
            for sub_field in field.setting_input_group_sub_fields:
                if sub_field.name not in row:
                    return "hack detected"
                    
            all_inserts.append( (0, 0, row ) )
            
        _logger.error(all_inserts)
        html_response.return_data = all_inserts
        html_response.history_data = all_inserts

        return html_response
        
    def _process_html_textbox(self, field, field_data):
        """Validation for textbox and preps for insertion into database"""
        html_response = html_field_response()
        html_response.error = ""
        
        #Required Check
        if field.setting_general_required == True and field_data == "":
            html_response.error = "Field Required"
        
        html_response.return_data = field_data
        html_response.history_data = field_data

        return html_response

    def _process_html_date_picker(self, field, field_data):
        """Validation for date picker textbox and preps for insertion into database"""
        html_response = html_field_response()
        html_response.error = ""

        #Required Check
        if field.setting_general_required == True and field_data == "":
            html_response.error = "Field Required"

        html_response.return_data = field_data
        html_response.history_data = field_data

        return html_response

    def _process_html_datetime_picker(self, field, field_data):
        """Validation for datetime picker textbox and preps for insertion into database"""
        html_response = html_field_response()
        html_response.error = ""

        #Required Check
        if field.setting_general_required == True and field_data == "":
            html_response.error = "Field Required"

        html_response.return_data = field_data
        html_response.history_data = field_data

        return html_response

    def _process_html_checkbox_boolean(self, field, field_data):
        """Validation for Checkboxes(Boolean) and preps for insertion into database"""
        html_response = html_field_response()
        html_response.error = ""

        #Required Check
        if field.setting_general_required == True and field_data == "":
            html_response.error = "Field Required"

        html_response.return_data = field_data
        html_response.history_data = field_data

        return html_response
        
    def _process_html_dropbox_m2o(self, field, field_data):
        """Validation for Dropbox(m2o) and preps for insertion into database"""
        html_response = html_field_response()
        html_response.error = ""

        #Required Check
        if field.setting_general_required == True and field_data == "":
            html_response.error = "Field Required"

        html_response.return_data = field_data
        html_response.history_data = field_data

        return html_response
        
    def _process_html_textarea(self, field, field_data):
        html_response = html_field_response()
        html_response.error = ""

        #Required Check
        if field.setting_general_required == True and field_data == "":
            html_response.error = "Field Required"

        html_response.return_data = field_data
        html_response.history_data = field_data

        return html_response

    def _process_html_radio_group_selection(self, field, field_data):
        html_response = html_field_response()
        html_response.error = ""

        #Required Check
        if field.setting_general_required == True and field_data == "":
            html_response.error = "Field Required"

        html_response.return_data = field_data
        html_response.history_data = field_data

        return html_response
    
    def _process_html_dropbox(self, field, field_data):
        """Validation for dropbox and preps for insertion into database"""
        html_response = html_field_response()
        html_response.error = ""

        #Required Check
        if field.setting_general_required == True and field_data == "":
            html_response.error = "Field Required"

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
        elif field.field_id.ttype == "many2one":
    
    	    html_response.error = ""
            html_response.return_data = field_data
            html_response.history_data = field_data
		    
    	    return html_response