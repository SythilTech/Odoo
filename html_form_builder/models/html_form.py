# -*- coding: utf-8 -*-
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models

class HtmlForm(models.Model):

    _name = "html.form"
    _description = "HTML Form"
    
    def _default_return_url(self):
        return request.httprequest.host_url + "form/thankyou"

    def _default_submit_url(self):
        return request.httprequest.host_url + "form/insert"
    
    name = fields.Char(string="Form Name", required=True)
    model_id = fields.Many2one('ir.model', string="Model", required=True)
    fields_ids = fields.One2many('html.form.field', 'html_id', string="HTML Fields")
    output_html = fields.Text(string='Embed Code', readonly=True)
    required_fields = fields.Text(readonly=True, string="Required Fields")
    defaults_values = fields.One2many('html.form.defaults', 'html_id', string="Default Values", help="Sets the value of an field before it gets inserted into the database")
    return_url = fields.Char(string="Return URL", default=_default_return_url, help="The URL that the user will be redirected to after submitting the form", required=True)
    submit_url = fields.Char(string="Submit URL", default=_default_submit_url)
        
    @api.onchange('model_id')
    def _onchange_model_id(self):
        #delete all existing fields
        for field_entry in self.fields_ids:
            field_entry.unlink()
        
        required_string = ""
        for model_field in self.env['ir.model.fields'].search([('model_id','=', self.model_id.id),('required','=',True) ]):
            required_string += model_field.field_description.encode("utf-8") + " (" + model_field.name.encode("utf-8") + ")\n"
        
        self.required_fields = required_string
    
    @api.one
    def generate_form(self):
        html_output = ""
        html_output += "<form method=\"POST\" action=\"" + self.submit_url + "\" enctype=\"multipart/form-data\">\n"
        html_output += "  <h1>" + self.name.encode("utf-8") + "</h1>\n"
                                 
        for fe in self.fields_ids:
            
            #each field type has it's own function that way we can make plugin modules with new field types
            method = '_generate_html_%s' % (fe.field_type.html_type,)
            action = getattr(self, method, None)
        
            if not action:
	        raise NotImplementedError('Method %r is not implemented on %r object.' % (method, self))
            
            html_output += action(fe)
 
	html_output += "  <input type=\"hidden\" name=\"form_id\" value=\"" + str(self.id) + "\"/>\n"
        html_output += "  <input type=\"submit\" value=\"Send\"/>\n"
    	html_output += "</form>\n"
        self.output_html = html_output

    def _generate_html_file_select(self, fe):
        html_output = ""
	html_output += "  <label for='" + fe.html_name.encode("utf-8") + "'>" + fe.field_label + "</label>\n"
		    		
	html_output += "  <input type=\"file\" id=\"" + fe.html_name.encode("utf-8") + "\" name=\"" + fe.html_name.encode("utf-8") + "\""

	if fe.field_id.required == True:
	    html_output += " required"
	
	html_output += "/><br/>\n"
	
	return html_output

    def _generate_html_textbox(self, fe):
        html_output = ""
        
        html_output += "  <label for='" + fe.html_name.encode("utf-8") + "'>" + fe.field_label + "</label>\n"
		    		
	html_output += "  <input type=\"text\" id=\"" + fe.html_name.encode("utf-8") + "\" name=\"" + fe.html_name.encode("utf-8") + "\""
		                                    
	if fe.field_id.required == True:
	    html_output += " required"
	
	html_output += "/><br/>\n"
	
	return html_output
	
    def _generate_html_textarea(self, fe):
        html_output = ""
	html_output += "  <label for='" + fe.html_name.encode("utf-8") + "'>" + fe.field_label + "</label>"
		    		
	html_output += "  <textarea id=\"" + fe.html_name.encode("utf-8") + "\" name=\"" + fe.html_name.encode("utf-8") + "\""
		                                    
	if fe.field_id.required == True:
	    html_output += " required"
	
	html_output += "/><br/>\n"
	
	return html_output
	
class HtmlFormField(models.Model):

    _name = "html.form.field"
    _description = "HTML Form Field"
    _order = "sequence asc"
        
    sequence = fields.Integer(string="Sequence")    
    html_id = fields.Many2one('html.form', ondelete='cascade', string="HTML Form")
    model_id = fields.Many2one('ir.model', string="Model", readonly=True)
    model = fields.Char(related="model_id.model", string="Model Name", readonly=True)
    field_id = fields.Many2one('ir.model.fields', domain="[('name','!=','create_date'),('name','!=','create_uid'),('name','!=','id'),('name','!=','write_date'),('name','!=','write_uid')]", string="Form Field")
    field_type = fields.Many2one('html.form.field.type', string="Field Type")
    field_label = fields.Char(string="Field Label")
    html_name = fields.Char(string="HTML Name")
    setting_general_required = fields.Boolean(string="Required")
    setting_binary_file_type_filter = fields.Selection([('image','Image'), ('audio','Audio')], string="File Type Filter")

    @api.model
    def create(self, values):
        sequence=self.env['ir.sequence'].get('sequence')
        values['sequence']=sequence
        return super(HtmlFormField, self).create(values)

    @api.onchange('field_id')
    def _onchange_field_id(self):
        """Set the default field type, html_name and field label"""
        if self.field_id:
            self.field_type = self.env['html.form.field.type'].search([('data_type','=',self.field_id.ttype), ('default','=',True)])[0].id
            self.html_name = self.field_id.name
            self.field_label = self.field_id.field_description
                  
class HtmlFormDefaults(models.Model):

    _name = "html.form.defaults"
    _description = "HTML Form Defaults"

    html_id = fields.Many2one('html.form', ondelete='cascade', string="HTML Form")
    model_id = fields.Many2one('ir.model', string="Model", readonly=True)
    model = fields.Char(related="model_id.model", string="Model Name", readonly=True)
    field_id = fields.Many2one('ir.model.fields', string="Form Fields")
    default_value = fields.Char(string="Default Value")

class HtmlFormFieldType(models.Model):

    _name = "html.form.field.type"
    _description = "HTML Form Field Type"
    
    name = fields.Char(string="Name")
    html_type = fields.Char(string="HTML Type", help="Internal Reference to this HTML type")
    data_type = fields.Char(string="Data Type", help="The Odoo data type(ttype)")
    default = fields.Boolean(string="Default", help="Is this the default HTML type for this datatype?")
        
class HtmlFormHistory(models.Model):

    _name = "html.form.history"
    _description = "HTML Form History"

    html_id = fields.Many2one('html.form', ondelete='cascade', string="HTML Form", readonly=True)
    form_name = fields.Char(related="html_id.name", string="Form Name")
    ref_url = fields.Char(string="Reference URL", readonly=True)
    record_id = fields.Integer(string="Record ID", readonly=True)
    insert_data = fields.One2many('html.form.history.field', 'html_id', string="HTML Fields", readonly=True)
    
class HtmlFormHistoryField(models.Model):

    _name = "html.form.history.field"
    _description = "HTML Form History Field"

    html_id = fields.Many2one('html.form.history', ondelete='cascade', string="HTML History Form")
    field_id = fields.Many2one('ir.model.fields', string="Field")
    insert_value = fields.Char(string="Insert Value")