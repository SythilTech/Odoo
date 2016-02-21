import openerp.http as http
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import base64
import json
import openerp

class HtmlFormControllerSnippets(openerp.addons.html_form_builder.controllers.main.HtmlFormController):


    @http.route('/form/updatefield', website=True, type='json', auth="user")
    def html_update_field(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value
        

        if int(values['html_field_id']) == 0:
            #create the field
            my_field = request.env['html.form.field'].create({'html_id':values['form_id'], 'field_id': values['field'], 'field_type': values['field_type'], 'html_name': values['html_name'], 'field_label': values['label'] })
            
            method = '_generate_html_%s' % (values['field_type'],)
            action = getattr(self, method, None)
        
            if not action:
	        raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))

            return {'field_id': my_field.id, 'html': action(my_field)}
            
            
        return "0"

    def _generate_html_textbox(self, field):
        """Generate textbox HTML"""
        html_output = ""        
        html_output += "<div class=\"form-group\">\n"
	html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\""
		    		
	if field.field_id.required == False:
	    html_output += " style=\"font-weight: normal\""
		    		
	html_output += ">" + field.field_label + "</label>\n"	    
	html_output += "  <input type=\"text\" class=\"form-control\" name=\"" + field.html_name.encode("utf-8") + "\""
		                                    
	if field.field_id.required == True:
	    html_output += " required"
	
	html_output += "/>\n"
	html_output += "</div>\n"
	
	return html_output

    def _generate_html_textarea(self, field):
        """Generate textarea HTML"""
        html_output = ""
        html_output += "<div class=\"form-group\">\n"
	html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\""
		    		
	if field.field_id.required == False:
	    html_output += " style=\"font-weight: normal\""
		    		
	html_output += ">" + field.field_label + "</label>\n"	    
	html_output += "  <textarea class=\"form-control\" name=\"" + field.html_name.encode("utf-8") + "\""
		                                    
	if field.field_id.required == True:
	    html_output += " required"
	
	html_output += "/>\n"
	html_output += "</div>\n"
	
	return html_output

    def _generate_html_dropbox(self, field):
        """Generates a dropbox"""
        html_output = ""
        
        if field.field_id.ttype == "selection":
            html_output += "<div class=\"form-group\">\n"
	    html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\""
		                
            if field.field_id.required == False:
                html_output += " style=\"font-weight: normal\""                
                		
            html_output += ">" + field.field_label
            html_output += "</label>\n"
	    html_output += "  <select class=\"form-control\" name=\"" + field.html_name.encode("utf-8") + "\""
                		    
	    if field.field_id.required == True:
	        html_output += " required"
	        
    	    html_output += ">\n"
    	    html_output += "    <option value=\"\">Select Option</option>\n"
    
    	    selection_list = dict(request.env[field.field_id.model_id.model]._columns[field.field_id.name].selection)
    	        
    	    for selection_value,selection_label in selection_list.items():
    	        html_output += "    <option value=\"" + selection_value.encode("utf-8") + "\">" + selection_label.encode("utf-8") + "</option>\n"
    	        
    	    html_output += "  </select>\n"
    	    html_output += "</div>\n"
    	    
    	    return html_output
    
    
    @http.route('/form/load', website=True, type='json', auth="public")
    def load_form(self, **kw):
        
        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value    
            
        html_form = request.env['html.form'].browse(int(values['form_id']) )
        
        form_string = ""
        form_string += "    <div class=\"container\">\n"
        form_string += "        <div class=\"row\">\n"
        form_string += "            <h2>" + html_form.name + "</h2>\n"
        form_string += "            <form method=\"POST\" action=\"" + html_form.submit_url + "\">\n"
        form_string += "                <div id=\"ehtml_fields\" class=\"oe_structure\">\n"

            
        for form_field in html_form.fields_ids:
            form_string += "<section data-form-type=\"" + form_field.field_type.html_type + "\" data-field-id=\"" + str(form_field.id) + "\" class=\"oe_snippet_body ehtml_form_field\">\n"

            method = '_generate_html_%s' % (form_field.field_type.html_type,)
	    action = getattr(self, method, None)
	    	        
	    if not action:
	        raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
	                
	    form_string += action(form_field)
	    form_string += "</section>\n"
	    	    
        form_string += "                </div>\n"
        form_string += "                <input type=\"hidden\" name=\"form_id\" value=\"" + str(html_form.id) + "\"/>\n"
        form_string += "                <input type=\"submit\" class=\"btn btn-primary btn-lg\" value=\"Send\"/>\n"
        form_string += "            </form>\n"
        form_string += "        </div>\n"
        form_string += "    </div>\n"

        return {'html_string': form_string}
            
    @http.route('/form/getfields', website=True, type='http', auth="public")
    def html_get_fields(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value        
        
        my_return = []        
        html_types = request.env['html.form.field.type'].search([('html_type','=',values['html_type'])])
        html_types_list = []
        
        for ht in html_types:
            html_types_list.append(ht.data_type)
            
        my_fields = request.env['ir.model.fields'].search([('model_id.model','=','res.partner'), ('field_description','=ilike',"%" + values['term'] + "%"), ('ttype','in',html_types_list)], limit=5)
        
        for my_field in my_fields:
            return_item = {"label": "[" + my_field.ttype + "] " + my_field.field_description + " (" + my_field.name + ")","description": my_field.field_description, "value": my_field.name, "id": my_field.id}
            my_return.append(return_item)
        
        return json.JSONEncoder().encode(my_return)
