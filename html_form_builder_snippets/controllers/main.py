# -*- coding: utf-8 -*-
import openerp.http as http
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import base64
import json
import openerp

class HtmlFormControllerSnippets(openerp.addons.html_form_builder.controllers.main.HtmlFormController):

    @http.route('/form/field/config/inputgroup', type="json", auth="user", website=True)
    def form_field_config_input_group(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value
            
        my_field = request.env['ir.model.fields'].browse( int(values['field_id']) )
        field_options_html = ""
        
        for field in request.env['ir.model.fields'].search([('model_id.model', '=', my_field.relation ), ('name','!=','display_name')] ):
            if (field.ttype == 'char' or field.ttype == 'integer' or field.ttype == 'selection'):
                field_options_html += "<input type=\"checkbox\" name=\"input_group_fields\" value=\"" + str(field.id) + "\"/> " + str(field.field_description) + " (" + str(field.ttype) + ")<br/>\n"
 
        return {'field_options_html': field_options_html }

    @http.route('/form/field/config/general', type="json", auth="user", website=True)
    def form_field_config_general(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value
            
        data_types_list = values['data_types']
            
        my_form = request.env['html.form'].browse( int(values['form_id']) )
            
        field_options_html = ""
        field_options_html = "<option value=\"\">Select Field</option>"
        
        for my_field in request.env['ir.model.fields'].search([('ttype', 'in', data_types_list ), ('model_id.model','=', values['form_model']), ('name','!=','display_name') ] ):
            field_options_html += "<option value=\"" + str(my_field.id) + "\">" + str(my_field.field_description) + " (" + str(my_field.name) + "/" + str(my_field.ttype) + ")" + "</option>\n"
 
        return {'field_options_html': field_options_html }

    @http.route('/form/captcha/load', type="json", auth="user", website=True)
    def html_captcha(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value
            
        html_form = request.env['html.form'].browse(int(values['form_id']) )
        
        html_form.captcha = int(values['captcha_id'])

        if 'client_key' in values:
            html_form.captcha_client_key = values['client_key']

        if 'client_secret' in values:
            html_form.captcha_secret_key = values['client_secret']
        
        html_string = ""
        html_string += "<div class=\"g-recaptcha\" data-sitekey=\"" + str(html_form.captcha_client_key) + "\"></div>"
                     
        return {'html_string': html_string}

    def _generate_html_date_picker(self, field):
        """Generate datepicker textbox HTML"""
        html_output = ""        
        html_output += "  <script>\n"
	html_output += "  $( function() {\n"
	html_output += "    $( \"#" + field.html_name.encode("utf-8") + "\" ).removeClass(\"hasDatepicker\");\n"
	html_output += "    $( \"#" + field.html_name.encode("utf-8") + "\" ).datetimepicker({pickTime: false, "
	
	if field.setting_date_format == "years":
	    html_output += "format: 'YYYY-01-01', minViewMode: 'years' });\n"

	if field.setting_date_format == "months":
	    html_output += "format: 'YYYY-MM-01', minViewMode: 'months' });\n"

	if field.setting_date_format == "days":
	    html_output += "format: 'YYYY-MM-DD', minViewMode: 'days' });\n"
	
	html_output += "  } );\n"
        html_output += "  </script>\n"
        
        html_output += "<div class=\"hff hff_date_picker form-group\" data-form-type=\"" + field.field_type.html_type + "\" data-field-id=\"" + str(field.id) + "\">\n"
	html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\">" + field.field_label + "</label>\n"
	html_output += "  <div class=\"input-group date\">\n"
	html_output += "    <input type=\"text\" class=\"form-control\" id=\"" + field.html_name.encode("utf-8") + "\" name=\"" + field.html_name.encode("utf-8") + "\""
		                                    
	if field.setting_general_required == True:
	    html_output += " required=\"required\""
	
	html_output += "/>\n"
	html_output += "    <span class=\"input-group-addon\"><span class=\"fa fa-calendar\"/></span>\n"
	html_output += "  </div>\n"
	html_output += "</div>\n"
	
	return html_output

    def _generate_html_datetime_picker(self, field):
        """Generate datetime picker textbox HTML"""
        html_output = ""        
        html_output += "  <script>\n"
	html_output += "  $( function() {\n"

	html_output += "    $( \"#" + field.html_name.encode("utf-8") + "\" ).removeClass(\"hasDatepicker\");\n"

        html_output += "    $(\"#" + field.html_name.encode("utf-8") + "\").on('click', function(e) {\n"
        html_output += "      $(e.currentTarget).closest(\"div.date\").datetimepicker({\n"
        html_output += "        useSeconds: true,\n"
        html_output += "        format: \"YYYY-MM-DD HH:mm:ss\",\n"
        html_output += "        icons : {\n"
        html_output += "          time: 'fa fa-clock-o',\n"
        html_output += "          date: 'fa fa-calendar',\n"
        html_output += "          up: 'fa fa-chevron-up',\n"
        html_output += "          down: 'fa fa-chevron-down'\n"
        html_output += "        },\n"
        html_output += "      });\n"
        html_output += "    });\n"

	html_output += "  } );\n"
        html_output += "  </script>\n"
        
        html_output += "<div class=\"hff hff_datetime_picker form-group\" data-form-type=\"" + field.field_type.html_type + "\" data-field-id=\"" + str(field.id) + "\">\n"
	html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\">" + field.field_label + "</label>\n"
	html_output += "  <div class=\"input-group date\">\n"
	html_output += "    <input type=\"text\" class=\"form-control\" id=\"" + field.html_name.encode("utf-8") + "\" name=\"" + field.html_name.encode("utf-8") + "\""
		                                    
	if field.setting_general_required == True:
	    html_output += " required=\"required\""
	
	html_output += "/>\n"
	html_output += "    <span class=\"input-group-addon\"><span class=\"fa fa-calendar\"/></span>\n"
	html_output += "  </div>\n"
	html_output += "</div>\n"
	
	return html_output
	
    def _generate_html_textbox(self, field):
        """Generate textbox HTML"""
        html_output = ""        
        html_output += "<div class=\"hff hff_textbox form-group\" data-form-type=\"" + field.field_type.html_type + "\" data-field-id=\"" + str(field.id) + "\">\n"
	html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\">" + field.field_label + "</label>\n"	    
	html_output += "  <input type=\""
	
	if field.validation_format == "email":
	    html_output += "email"
	else:
	    html_output += "text"
	
	html_output += "\" class=\"form-control\" name=\"" + field.html_name.encode("utf-8") + "\""
		                                    
	if field.setting_general_required == True:
	    html_output += " required=\"required\""
	
	if field.validation_format == "lettersonly":
	    html_output +=  ' pattern="[a-zA-Z ]+" title="Letters Only"'
	
	if field.character_limit > 0:
	    html_output += ' maxlength="' + str(field.character_limit) + '"'
	
	html_output += "/>\n"
	html_output += "</div>\n"
	
	return html_output

    def _generate_html_textarea(self, field):
        """Generate textarea HTML"""
        html_output = ""
        html_output += "<div class=\"hff hff_textarea form-group\" data-form-type=\"" + field.field_type.html_type + "\" data-field-id=\"" + str(field.id) + "\">\n"
	html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\">" + field.field_label + "</label>\n"	    
	html_output += "  <textarea class=\"form-control\" name=\"" + field.html_name.encode("utf-8") + "\""
		                                    
	if field.setting_general_required == True:
	    html_output += " required=\"required\""
	
	html_output += "/>\n"
	html_output += "</div>\n"
	
	return html_output

    def _generate_html_file_select(self, field):
        """Generate Binary HTML"""
        html_output = ""

        #html_output += "<div class=\"hff hff_binary form-group\" data-form-type=\"" + field.field_type.html_type + "\" data-field-id=\"" + str(field.id) + "\">\n"
	#html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\">" + field.field_label + "</label>\n"
        #html_output += "  <div class=\"input-group\">\n"
        #html_output += "    <label class=\"input-group-btn\">\n"
        #html_output += "      <span class=\"btn btn-primary\">\n"
        #html_output += "        Browse... <input type=\"file\" style=\"display: none;\"/>\n"
        #html_output += "      </span>\n"
        #html_output += "    </label>\n"
        #html_output += "    <input type=\"text\" class=\"form-control\" readonly=\"\"/>\n"
        #html_output += "  </div>\n"
        #html_output += "</div>\n"

        html_output += "<div class=\"hff hff_binary form-group\" data-form-type=\"" + field.field_type.html_type + "\" data-field-id=\"" + str(field.id) + "\">\n"
	html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\">" + field.field_label + "</label>\n"
        html_output += "  <input name=\"" + field.html_name.encode("utf-8") + "\" type=\"file\"/>\n"
        html_output += "</div>\n"
              
	return html_output

    def _generate_html_input_group(self, field):
        """Generate input group HTML"""
        html_output = ""
 
        html_output += "<script>\n"
        html_output += "  $(function() {\n"
        html_output += "    $( \"#" + field.html_name.encode("utf-8") + "_add\" ).click(function(e) {\n"
        html_output += "      e.preventDefault();\n"
        html_output += "      $( \"#" + field.html_name.encode("utf-8") + "_container\" ).append( '<div class=\"row form-group\">' + $( \"#" + field.html_name.encode("utf-8") + "_placeholder\").html() + '</div>');\n"
        html_output += "    });\n"
        html_output += "  });\n"
        html_output += "</script>\n"

        sub_field_number = len(field.setting_input_group_sub_fields)
        column_width = 12 / sub_field_number

        html_output += "<div class=\"hff hff_input_group form-group\" data-sub-field-number=\"" + str(sub_field_number) + "\" data-html-name=\"" + field.html_name.encode("utf-8") + "\" data-form-type=\"" + field.field_type.html_type + "\" data-field-id=\"" + str(field.id) + "\">\n"
	html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\">" + field.field_label + "</label><br/>\n"
        
        html_output += "  <div id=\"" + str(field.html_name) + "_container\">\n"
        html_output += "    <div id=\"" + str(field.html_name) + "_placeholder\" class=\"row form-group\">\n"
        
        for sub_field in field.setting_input_group_sub_fields:
            if sub_field.ttype == "char" or sub_field.ttype == "integer":
                html_output += "      <div class=\"col-md-" + str(column_width) + "\"><input type=\"text\" class=\"form-control\" data-sub-field-name=\"" + str(sub_field.name) + "\" placeholder=\"" + str(sub_field.field_description) + "\"/></div>\n"
            elif sub_field.ttype == "selection":
                html_output += "      <div class=\"col-md-" + str(column_width) + "\">\n"
                html_output += "<select class=\"form-control\" data-sub-field-name=\"" + str(sub_field.name) + "\" placeholder=\"" + str(sub_field.field_description) + "\">\n"
                
                   	    
                selection_list = dict(request.env[sub_field.model_id.model]._columns[sub_field.name].selection)

                html_output += "<option value=\"\">" + sub_field.field_description + "</option>\n"
     	        
		for selection_value,selection_label in selection_list.items():
                    html_output += "<option value=\"" + selection_value.encode("utf-8") + "\">" + selection_label + "</option>\n"

                html_output += "</select>\n"
                html_output += "</div>\n"


	html_output += "    </div>\n"
        html_output += "  </div>\n"
        
        html_output += "  <div class=\"col-md-12\">\n"
        html_output += "    <button class=\"btn btn-primary btn-md row pull-right\" id=\"" + field.html_name.encode("utf-8") + "_add\">Add (+)</button>\n"
        html_output += "  </div>\n"

	html_output += "</div>\n"
	
	return html_output

    def _generate_html_radio_group_selection(self, field):
        """Generate Radio Group(Selection) HTML"""
        html_output = ""
        html_output += "<div class=\"hff hff_radio_group form-group\" data-form-type=\"" + field.field_type.html_type + "\" data-field-id=\"" + str(field.id) + "\">\n"

    	if field.setting_radio_group_layout_type == "multi":
	    html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\">" + field.field_label + "</label>\n"
    	if field.setting_radio_group_layout_type == "single":
	    html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\">" + field.field_label + "</label><br/>\n"

    	selection_list = dict(request.env[field.field_id.model_id.model]._columns[field.field_id.name].selection)
    	        
    	for selection_value,selection_label in selection_list.items():
    	    if field.setting_radio_group_layout_type == "multi":
    	       html_output += "  <div class=\"radio\">\n"
    	    if field.setting_radio_group_layout_type == "single":
    	       html_output += "  <div class=\"radio-inline\">\n"
    	    
    	    html_output += "    <label><input type=\"radio\" name=\"" + field.html_name.encode("utf-8") + "\" value=\"" + selection_value.encode("utf-8") + "\"/>" + selection_label.encode("utf-8") + "</label>\n"
    	    html_output += "  </div>\n"
    	    
	html_output += "\n"	
	html_output += "</div>\n"
	
	return html_output

    def _generate_html_checkbox_group(self, field):
        """Generate Checkbox Group HTML"""
        html_output = ""
        html_output += "<div class=\"hff hff_checkbox_group\" data-form-type=\"" + field.field_type.html_type + "\" data-field-id=\"" + str(field.id) + "\">\n"
        html_output += "  <label for=\"" + field.html_name.encode("utf-8") + "\">" + field.field_label + "</label>\n"
	
	for my_record in request.env[field.field_id.relation].search([('name','!=','')]):
	    html_output += "  <div class=\"checkbox\">\n"
	    html_output += "    <label><input type=\"checkbox\" value=\"" + str(my_record.id) + "\" name=\"" + field.html_name.encode("utf-8") + "\"/>" + my_record.name.encode("utf-8") + "</label>\n"
	    html_output += "  </div>\n"
	
	html_output += "</div>\n"
	
	return html_output

    def _generate_html_checkbox_boolean(self, field):
        """Generate Checkbox(Boolean) HTML"""
        html_output = ""
        html_output += "<div class=\"hff hff_checkbox checkbox\" data-form-type=\"" + field.field_type.html_type + "\" data-field-id=\"" + str(field.id) + "\">\n"
	html_output += "  <label><input type=\"checkbox\" name=\"" + field.html_name.encode("utf-8") + "\"/>" + field.field_label + "</label>\n"
	html_output += "</div>\n"
	
	return html_output

    def _generate_html_dropbox(self, field):
        """Generates a dropbox(Selection and many2one)"""
        html_output = ""
        
        html_output += "<div class=\"hff hff_dropbox form-group\" data-form-type=\"" + field.field_type.html_type + "\" data-field-id=\"" + str(field.id) + "\">\n"
	html_output += "  <label class=\"control-label\" for=\"" + field.html_name.encode("utf-8") + "\">" + field.field_label
        html_output += "</label>\n"
	html_output += "  <select class=\"form-control\" name=\"" + field.html_name.encode("utf-8") + "\""
                		    
	if field.setting_general_required == True:
	    html_output += " required=\"required\""
	        
    	html_output += ">\n"
    	html_output += "    <option value=\"\">Select Option</option>\n"

        if field.field_id.ttype == "selection":
    
    	    selection_list = dict(request.env[field.field_id.model_id.model]._columns[field.field_id.name].selection)
    	        
    	    for selection_value,selection_label in selection_list.items():
    	        html_output += "    <option value=\"" + selection_value.encode("utf-8") + "\">" + selection_label.encode("utf-8") + "</option>\n"
    	        
    	elif field.field_id.ttype == "many2one":
            selection_list = request.env[field.field_id.relation].search([])
    	        
    	    for row in selection_list:
    	        html_output += "    <option value=\"" + str(row.id) + "\">" + row.name + "</option>\n"
    	        
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
        form_string += "  <div class=\"container mt16 mb16\">\n"
        form_string += "    <h2>" + html_form.name + "</h2>\n"
        form_string += "    <form role=\"form\" method=\"POST\" action=\"" + html_form.submit_url + "\">\n"
        form_string += "      <div class=\"oe_structure\" id=\"html_fields\">\n"
            
        for form_field in html_form.fields_ids:

            method = '_generate_html_%s' % (form_field.field_type.html_type,)
	    action = getattr(self, method, None)
	    	        
	    if not action:
	        raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
	                
	    form_string += action(form_field)	    	    
	    	    
        if html_form.captcha:
            form_string += "<div class=\"html_form_captcha col-md-12 form-group\" data-captcha-id=\"" + str(html_form.captcha.id) + "\">\n"
            form_string += "  <div class=\"g-recaptcha\" data-sitekey=\"" + str(html_form.captcha_client_key) + "\"></div>\n"
            form_string += "</div>\n"
	    	    
	    	    
        form_string += "      </div>\n"
        form_string += "      <input type=\"hidden\" name=\"form_id\" value=\"" + str(html_form.id) + "\"/>\n"
	form_string += "      <input type=\"hidden\" name=\"csrf_token\"/>\n"
	form_string += "      <input style=\"display:none;\" name=\"my_pie\" value=\"3.14\"/>\n"	
        form_string += "      <button class=\"btn btn-primary btn-lg\">Submit</button>\n"
        form_string += "    </form>\n"
        form_string += "  </div>\n"

        return {'html_string': form_string, 'form_model': html_form.model_id.model }

    @http.route('/form/new', website=True, type='json', auth="public")
    def new_form(self, **kw):
        
        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value    
        
        
        action = request.env['html.form.snippet.action'].browse(int(values['action_id']) )

        my_model = request.env['ir.model'].search([('model','=',action.action_model)])
        html_form = request.env['html.form'].create({'name': 'My New Form', 'model_id': my_model.id })
        
        form_string = ""
        form_string += "  <div class=\"container mt16 mb16\">\n"
        form_string += "    <h2>" + html_form.name + "</h2>\n"
        form_string += "    <form role=\"form\" method=\"POST\" action=\"" + html_form.submit_url + "\">\n"
        form_string += "      <div class=\"oe_structure\" id=\"html_fields\"/>\n"
        form_string += "      <input type=\"hidden\" name=\"form_id\" value=\"" + str(html_form.id) + "\"/>\n"
	form_string += "      <input type=\"hidden\" name=\"csrf_token\"/>\n"
	form_string += "      <input style=\"display:none;\" name=\"my_pie\" value=\"3.14\"/>\n"
        form_string += "      <button class=\"btn btn-primary btn-lg\">Submit</button>\n"
        form_string += "    </form>\n"
        form_string += "  </div>\n"

        return {'html_string': form_string, 'form_model': action.action_model, 'form_id': html_form.id }

    @http.route('/form/fieldtype', website=True, type='json', auth="public")
    def form_fieldtype(self, **kw):
        
        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value    
            
        field_type = request.env['html.form.field.type'].search( [ ('html_type', '=', values['field_type'] ) ] )[0]
        
        return {'field_type': field_type.data_type }

            
    @http.route('/form/field/add', website=True, type='json', auth="user")
    def form_add_field(self, **kw):

        values = {}
	for field_name, field_value in kw.items():
            values[field_name] = field_value
                    
        field_id = request.env['ir.model.fields'].browse( int(values['field_id']) )
        
        #Don't add the same field twice to this form
        if len(request.env['html.form.field'].search([('html_id','=', int(values['form_id']) ), ('field_id','=',field_id.id)])) > 0:
            return {'html_string': "Field already added"}
        
        field_type = request.env['html.form.field.type'].search([('html_type','=', values['html_type'] )])[0]

        insert_values = {}
        insert_values['html_id'] = int(values['form_id'])
        insert_values['field_id'] = field_id.id
        insert_values['field_type'] = field_type.id
        insert_values['html_name'] = field_id.name
        insert_values['field_label'] = field_id.field_description
        if 'format_validation' in values: insert_values['validation_format'] = values['format_validation']
        if 'character_limit' in values: insert_values['character_limit'] = values['character_limit']
        if 'setting_general_required' in values: insert_values['setting_general_required'] = values['field_required']
        if 'layout_type' in values: insert_values['setting_radio_group_layout_type'] = values['layout_type']        
        if 'setting_date_format' in values: insert_values['setting_date_format'] = values['setting_date_format']
        if 'sub_fields' in values: insert_values['setting_input_group_sub_fields'] = [(6, 0, [int(i) for i in values['sub_fields'] ] )]

        form_field = request.env['html.form.field'].create(insert_values)
        
        form_string = ""

        method = '_generate_html_%s' % (values['html_type'],)
	action = getattr(self, method, None)
	    	        
	if not action:
	    raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
	                
	form_string += action(form_field)
        
        return {'html_string': form_string}