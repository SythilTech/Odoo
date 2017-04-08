from openerp import models, fields, api
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)
import cgi

class EhtmlFormgen(models.Model):

    _name = "ehtml.formgen"    
    
    def _default_return_url(self):
        return request.httprequest.host_url + "form/thankyou"    
    
    name = fields.Char(string="Form Name", required=True)
    model_id = fields.Many2one('ir.model', string="Model", required=True)
    fields_ids = fields.One2many('ehtml.fieldentry', 'html_id', string="HTML Fields")
    output_html = fields.Text(string='Embed Code', readonly=True)
    required_fields = fields.Text(readonly=True, string="Required Fields")
    defaults_values = fields.One2many('ehtml.fielddefault', 'html_id', string="Default Values", help="Sets the value of an field before it gets inserted into the database")
    return_url = fields.Char(string="Return URL", default=_default_return_url, help="The URL that the user will be redirected to after submitting the form", required=True)
    form_type = fields.Selection([('reg','Plain'),('odoo','Odoo Website')], default="odoo", string="Form Type")
        
    @api.onchange('model_id')
    @api.one
    def change_model(self):
        #delete all existing fields
        for field_entry in self.fields_ids:
            field_entry.unlink()
        
        required_string = ""
        for model_field in self.env['ir.model.fields'].search([('model_id','=', self.model_id.id),('required','=',True) ]):
            required_string += model_field.field_description.encode("utf-8") + " (" + model_field.name.encode("utf-8") + ")\n"
        
        self.required_fields = required_string

    @api.one
    def generate_form(self):
        if self.form_type == 'reg':
            self.generate_form_reg()
        elif self.form_type == 'odoo':
            self.generate_form_odoo()
        else:
            self.generate_form_optimize()
            
    @api.one
    def generate_form_reg(self):
        html_output = ""
        html_output += "<link href=\"http://code.jquery.com/ui/1.10.4/themes/ui-lightness/jquery-ui.css\" rel=\"stylesheet\">\n";
	html_output += "<script src=\"http://code.jquery.com/jquery-1.10.2.js\"></script>\n";
        html_output += "<script src=\"http://code.jquery.com/ui/1.10.4/jquery-ui.js\"></script>\n";
        html_output += '<div id="ehtml_form">' + "\n"
        html_output += '<form method="POST" action="' + request.httprequest.host_url + 'form/myinsert">' + "\n"
        for fe in self.fields_ids:              
            html_output += '<label for="' + fe.html_name + '">' + fe.field_id.field_description
                
            if fe.field_id.required == True:
                html_output += ' *'
                
            html_output += '</label><br/>\n'
                
            if fe.html_field_type == "text":
                html_output += '<input type="text" id="' + fe.html_name + '" name="' + fe.html_name + '"'
                    
                if fe.field_id.size > 0:
                    html_output += ' maxlength="' + fe.field_id.size + '"'
                    
                if fe.field_id.required == True:
                    html_output += ' required'
                
                html_output += '/><br>\n'
                    
            if fe.html_field_type == "textarea":
                html_output += '<textarea id="' + fe.html_name + '" name="' + fe.html_name + '"'
                   
                if fe.field_id.required == True:
    	            html_output += ' required'
    	            
    	        html_output += '></textarea><br>\n'
    	        
    	    if fe.html_field_type == "number":
	        html_output += '<input type="number" id="' + fe.html_name + '" name="' + fe.html_name + '"'
		    
	        if fe.field_id.required == True:
	            html_output += ' required'        
		    	            
    	        html_output += '/><br>\n'
    	    
    	    if fe.html_field_type == "search":
                html_output += "<script>\n"
                html_output += "$(document).ready(function() {\n"
                html_output += '    $("#' + fe.html_name + '").autocomplete({' + "\n"
                html_output += "        source: function( request, response ) {\n"
                html_output += '            $.ajax({url: "' + request.httprequest.host_url + 'form/autocomplete?callback=?",dataType: "jsonp",' + "\n"
                html_output += '            data: {'+ "\n"
                html_output += "                q: request.term\n"
                html_output += "            },\n"
                html_output += "            success: function( data ) {\n"
                html_output += "                response( data );\n"
                html_output += "            }});\n"
                html_output += "        }\n"
                html_output += "    });\n"
                html_output += "});\n"
                html_output += "</script>\n"
                html_output += '<input type="search" id="' + fe.html_name + '" name="' + fe.html_name + '"'
		    
	        if fe.field_id.required == True:
	            html_output += ' required'        
		    	            
    	        html_output += '/><br>\n'
    	    
    	    html_output += "<br>\n"
    	html_output += '<input type="hidden" name="form_id" value="' + str(self.id) + '"/>' + "\n"
    	html_output += '<input type="submit" value="Submit Form"/>' + "\n"
    	html_output += "</form>\n"
        html_output += "</div>"
        self.output_html = html_output
       
    @api.one
    def generate_form_odoo(self):
        html_output = ""
        html_output += "<section id=\"ehtml_form\" class=\"oe_snippet_body ehtml_form container\">\n"
        html_output += '  <form method="POST" action="' + request.httprequest.host_url + 'form/myinsert" enctype=\"multipart/form-data\">' + "\n"
        html_output += "    <h1>" + self.name.encode("utf-8") + "</h1>\n"
        html_output += "    <div id=\"ehtml_fields\" class=\"oe_structure\">\n"
                                 
        for fe in self.fields_ids:
            html_output += "      <section class=\"oe_snippet_body ehtml_form_field\">\n"            
            
            if fe.html_field_type == "text":
                html_output += "        <div class=\"form-group\">\n"
		html_output += "          <label class=\"control-label\" for=\"" + fe.html_name + "\""
		
                if fe.field_id.required == False:
                    html_output += ' style="font-weight: normal"'		
		
		html_output += ">" + fe.field_label + "</label>\n"
                
                html_output += '          <input type="text" class="form-control" id="' + fe.html_name + '" name="' + fe.html_name + '"'
                
                if fe.field_id.size > 0:
                    html_output += ' maxlength="' + fe.field_id.size + '"'
                    
                if fe.field_id.required == True:
                    html_output += ' required="required"'
                
                html_output += "/>\n"
                html_output += "        </div>\n"
            if fe.html_field_type == "textarea":
                html_output += "        <div class=\"form-group\">\n"
		html_output += "          <label class=\"control-label\" for=\"" + fe.html_name + "\""
		                
                if fe.field_id.required == False:
                    html_output += ' style="font-weight: normal"'         
                
		html_output += ">" + fe.field_label + "</label>\n"
                html_output += '          <textarea class="form-control" id="' + fe.html_name + '" name="' + fe.html_name + '"'
                                
                if fe.field_id.required == True:
    	            html_output += ' required'
    	            
    	        html_output += "></textarea>\n"
    	        
    	        html_output += "        </div>\n"
            if fe.html_field_type == "binary":
                html_output += "        <div class=\"form-group\">\n"
		html_output += "          <label class=\"control-label\" for=\"" + fe.html_name + "\""
		
                if fe.field_id.required == False:
                    html_output += ' style="font-weight: normal"'		
		
		html_output += ">" + fe.field_label + "</label>\n"

                html_output += '          <input type="file" id="' + fe.html_name + '" name="' + fe.html_name + '"'
                                
                if fe.field_id.required == True:
    	            html_output += ' required'
    	            
    	        html_output += "/>\n"
    	        
    	        html_output += "        </div>\n"
 
    	    if fe.html_field_type == "checkbox":
	        html_output += "        <div class=\"checkbox\">\n"
	        html_output += "          <label class=\"control-label\""
	                        
                if fe.field_id.required == False:
                    html_output += ' style="font-weight: normal"'
	        
	        html_output += ">\n"
	        
	                        
	        html_output += '          <input type="checkbox" id="' + fe.html_name + '" name="' + fe.html_name + '"'
                                	                       
	        if fe.field_id.required == True:
	            html_output += ' required'
	        	            
	        html_output += '/>' + fe.field_label + "\n"
	        
	        html_output += "          </label>\n"
	        html_output += "        </div>\n"
    	    
    	    if fe.html_field_type == "number":
                html_output += "        <div class=\"form-group\">\n"
		html_output += "          <label class=\"control-label\" for=\"" + fe.html_name + "\""
		
                
                if fe.field_id.required == False:
                    html_output += ' style="font-weight: normal"'		
		
		html_output += ">" + fe.field_label + "</label>\n"                	        
	        
	        html_output += '          <input type="number" class="form-control" id="' + fe.html_name + '" name="' + fe.html_name + '"'
                                		    
	        if fe.field_id.required == True:
	            html_output += ' required'        
		    	            
    	        html_output += "/>\n"
    	        html_output += "        </div>\n"
    	    if fe.html_field_type == "selection":
                html_output += "        <div class=\"form-group\">\n"
		html_output += "          <label class=\"control-label\" for=\"" + fe.html_name + "\""
		                
                if fe.field_id.required == False:
                    html_output += ' style="font-weight: normal"'                
                		
		html_output += ">" + fe.field_label
                
                                    
                html_output += "</label>\n"
	        html_output += '          <select class="form-control" id="' + fe.html_name + '" name="' + fe.html_name + '"'
                		    
	        if fe.field_id.required == True:
	            html_output += ' required'        
		    	            
    	        html_output += ">\n"

    	        html_output += "            <option value=\"\">Select Option</option>\n"

    	        
    	        selection_list = dict(self.env[self.model_id.model]._columns[fe.field_id.name].selection)
    	        
    	        for selection_value,selection_label in selection_list.items():
    	            html_output += "            <option value=\"" + str(selection_value) + "\">" + str(selection_label) + "</option>\n"
    	        
    	        html_output += "          </select>\n"
    	        html_output += "        </div>\n"
    	        	    

    	    if fe.html_field_type == "radiobuttons":
                
                html_output += "      <label class=\"control-label\""
                
                if fe.field_id.required == False:
                    html_output += ' style="font-weight: normal"'                
                
                html_output += ">" + fe.field_label + "</label>\n"
    	        
    	        selection_list = dict(self.env[self.model_id.model]._columns[fe.field_id.name].selection)
    	        
    	        for selection_value,selection_label in selection_list.items():
    	            html_output += "        <div class=\"radio\">\n"
    	            
    	            
    	            html_output += "          <label><input type=\"radio\" name=\"" + fe.html_name + "\" value=\"" + str(selection_value) + "\""
    	            
    	            if fe.field_id.required == True:
		        html_output += ' required'
    	            
    	            html_output += "/>" + str(selection_label) + "</label>\n"
    	            html_output += "        </div>\n"
    	            
    	    if fe.html_field_type == "dropdownstatic":
                html_output += "        <div class=\"form-group\">\n"
		html_output += "          <label class=\"control-label\" for=\"" + fe.html_name + "\""
		                
                if fe.field_id.required == False:
                    html_output += ' style="font-weight: normal"'		
		
		html_output += ">" + fe.field_label                                
                    
                html_output += "</label>\n"
	        html_output += '          <select class="form-control" id="' + fe.html_name + '" name="' + fe.html_name + '"'
		    
	        if fe.field_id.required == True:
	            html_output += ' required'
		    	            
    	        html_output += ">\n"
    	        
    	        for reco in self.env[str(fe.field_id.relation)].search([]):
    	            html_output += "            <option value=\"" + str(reco.id) + "\">" + unicode(cgi.escape(reco.name)) + "</option>\n"
    	        
    	        html_output += "          </select>\n"
    	        html_output += "        </div>\n"
            
            html_output += "      </section>\n"
	html_output += '      <input type="hidden" name="form_id" value="' + str(self.id) + '"/>' + "\n"
        html_output += "      <input type=\"submit\" class=\"btn btn-primary btn-lg\" value=\"Send\"/>\n"
        
        html_output += "    </div>\n"
    	html_output += "  </form>\n"
        html_output += "</section>\n"
        self.output_html = html_output

class EhtmlFieldEntry(models.Model):

    _name = "ehtml.fieldentry"
    _order = "sequence asc"
    
    sequence = fields.Integer(string="Sequence")
    html_id = fields.Many2one('ehtml.formgen', string="HTML Form")
    model_id = fields.Many2one('ir.model', string="Model", required=True)
    model = fields.Char(related="model_id.model", string="Related Model")
    field_id = fields.Many2one('ir.model.fields', domain="[('name','!=','create_date'),('name','!=','create_uid'),('name','!=','id'),('name','!=','write_date'),('name','!=','write_uid')]", string="Form Field")
    field_label = fields.Char(string="Field Label")
    html_name = fields.Char(string="HTML Field Name")
    html_field_type = fields.Selection((('binary','Binary'),('text','Textbox'),('textarea','Textarea'),('number','Number'),('selection','Selection'),('radiobuttons','Radiobuttons'),('checkbox','Checkbox'),('search','Search'),('dropdownstatic','Dropdown(static)') ), string="HTML Field Type")
    
    @api.model
    def create(self, values):
        sequence=self.env['ir.sequence'].get('sequence')
        values['sequence']=sequence
        return super(EhtmlFieldEntry, self).create(values)
                
    @api.onchange('field_id')
    def update_html_name(self):
        self.html_name = self.field_id.name
        self.field_label = self.field_id.field_description

        if (self.field_id.ttype == "binary"):
	    self.html_field_type = "binary"

        if (self.field_id.ttype == "boolean"):
	    self.html_field_type = "checkbox"        

        if (self.field_id.ttype == "selection"):
	    self.html_field_type = "selection"        
        
        if (self.field_id.ttype == "char"):
            self.html_field_type = "text"
            
        if (self.field_id.ttype == "text"):
	    self.html_field_type = "textarea"
        
        if (self.field_id.ttype == "integer"):
            self.html_field_type = "number"
            
        if (self.field_id.ttype == "many2one"):
	    self.html_field_type = "dropdownstatic"
        
class EhtmlFieldDefault(models.Model):

    _name = "ehtml.fielddefault"

    html_id = fields.Many2one('ehtml.formgen', string="HTML Form")
    model_id = fields.Many2one('ir.model', string="Model", required=True)
    model = fields.Char(related="model_id.model", string="Model Name")
    field_id = fields.Many2one('ir.model.fields', string="Form Fields")
    default_value = fields.Char(string="Default Value")
    
class EhtmlHistory(models.Model):

    _name = "ehtml.history"

    html_id = fields.Many2one('ehtml.formgen', string="HTML Form", readonly=True)
    ref_url = fields.Char(string="Reference URL", readonly=True)
    record_id = fields.Integer(string="Record ID", readonly=True)
    form_name = fields.Char(string="Form Name", related="html_id.name")
    insert_data = fields.One2many('ehtml.fieldinsert', 'html_id', string="HTML Fields", readonly=True)
    
class EhtmlFieldInsert(models.Model):

    _name = "ehtml.fieldinsert"

    html_id = fields.Many2one('ehtml.history')
    field_id = fields.Many2one('ir.model.fields', string="Field")
    insert_value = fields.Char(string="Insert Value")
    