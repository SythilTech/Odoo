from openerp import models, fields, api, tools
import logging
_logger = logging.getLogger(__name__)
import requests
from datetime import datetime
from urllib import urlencode, quote as quote


try:
    # We use a jinja2 sandboxed environment to render mako templates.
    # Note that the rendering does not cover all the mako syntax, in particular
    # arbitrary Python statements are not accepted, and not all expressions are
    # allowed: only "public" attributes (not starting with '_') of objects may
    # be accessed.
    # This is done on purpose: it prevents incidental or malicious execution of
    # Python code that may break the security of the server.
    from jinja2.sandbox import SandboxedEnvironment
    mako_template_env = SandboxedEnvironment(
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="${",
        variable_end_string="}",
        comment_start_string="<%doc>",
        comment_end_string="</%doc>",
        line_statement_prefix="%",
        line_comment_prefix="##",
        trim_blocks=True,               # do not output newline after blocks
        autoescape=True,                # XML/HTML automatic escaping
    )
    mako_template_env.globals.update({
        'str': str,
        'quote': quote,
        'urlencode': urlencode,
        'datetime': datetime,
        'len': len,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'filter': filter,
        'reduce': reduce,
        'map': map,
        'round': round,

        # dateutil.relativedelta is an old-style class and cannot be directly
        # instanciated wihtin a jinja2 expression, so a lambda "proxy" is
        # is needed, apparently.
        'relativedelta': lambda *a, **kw : relativedelta.relativedelta(*a, **kw),
    })
except ImportError:
    _logger.warning("jinja2 not available, templating features will not work!")


class esms_templates(models.Model):

    _name = "esms.templates"
    
    name = fields.Char(required=True, string='Template Name')
    model_id = fields.Many2one('ir.model', string='Applies to', help="The kind of document with with this template can be used")
    model = fields.Char(related="model_id.model", string='Related Document Model', select=True, store=True, readonly=True)
    template_body = fields.Text('Body', translate=True, sanitize=False, help="Plain text version of the message (placeholders may be used here)")
    sms_from = fields.Char(string='From (Mobile)', help="Sender mobile number (placeholders may be used here). If not set, the default value will be the author's mobile number.")
    sms_to = fields.Char(string='To (Mobile)', help="To mobile number (placeholders may be used here)")
    account_gateway = fields.Many2one('esms.accounts', string="Account")    
    model_object_field = fields.Many2one('ir.model.fields', string="Field", help="Select target field from the related document model.\nIf it is a relationship field you will be able to select a target field at the destination of the relationship.")
    sub_object = fields.Many2one('ir.model', string='Sub-model', readonly=True, help="When a relationship field is selected as first field, this field shows the document model the relationship goes to.")
    sub_model_object_field = fields.Many2one('ir.model.fields', string='Sub-field', help="When a relationship field is selected as first field, this field lets you select the target field within the destination document model (sub-model).")
    null_value = fields.Char(string='Default Value', help="Optional value to use if the target field is empty")
    copyvalue = fields.Char(string='Placeholder Expression', help="Final placeholder expression, to be copy-pasted in the desired template field.")
    lang = fields.Char(string='Language', help="Optional translation language (ISO code) to select when sending out an email. If not set, the english version will be used. This should usually be a placeholder expression that provides the appropriate language, e.g. ${object.partner_id.lang}.", placeholder="${object.partner_id.lang}")
    from_mobile = fields.Many2one('esms.verified.numbers', string="From Mobile")

    @api.model
    def send_template(self, template_id, record_id):
        my_template = self.env['esms.templates'].browse(template_id)
        sms_rendered_content = self.env['esms.templates'].render_template(my_template.template_body, my_template.model_id.model, record_id)
        
        rendered_sms_to = self.env['esms.templates'].render_template(my_template.sms_to, my_template.model_id.model, record_id)
         
        gateway_model = my_template.from_mobile.account_id.account_gateway.gateway_model_name
        
	my_sms = self.env[gateway_model].send_message(my_template.from_mobile.account_id.id, my_template.from_mobile.mobile_number, rendered_sms_to, sms_rendered_content, my_template.model_id.model, record_id)
	
    def render_template(self, template, model, res_id):
        """Render the given template text, replace mako expressions ``${expr}``
           with the result of evaluating these expressions with
           an evaluation context containing:

                * ``user``: browse_record of the current user
                * ``object``: browse_record of the document record this mail is
                              related to
                * ``context``: the context passed to the mail composition wizard

           :param str template: the template text to render
           :param str model: model name of the document record this mail is related to.
           :param int res_id: id of document records those mails are related to.
        """
        
        # try to load the template
        #try:
        template = mako_template_env.from_string(tools.ustr(template))
        #except Exception:
        #    _logger.error("Failed to load template %r", template)
        #    return False

        # prepare template variables
        user = self.env.user
        record = self.env[model].browse(res_id)
        
        variables = {
            'user': user
        }
        
        
        
        variables['object'] = record
        try:
            render_result = template.render(variables)
        except Exception:
            _logger.error("Failed to render template %r using values %r" % (template, variables))
            render_result = u""
        if render_result == u"False":
            render_result = u""

        return render_result
            
    @api.v7
    def onchange_model_id(self, cr, uid, ids, model_id, context=None):
        mod_name = False
        if model_id:
            mod_name = self.pool.get('ir.model').browse(cr, uid, model_id, context).model
        return {'value': {'model': mod_name}}

    @api.v7
    def onchange_sub_model_object_value_field(self, cr, uid, ids, model_object_field, sub_model_object_field=False, null_value=None, context=None):
        result = {
            'sub_object': False,
            'copyvalue': False,
            'sub_model_object_field': False,
            'null_value': False
            }
        if model_object_field:
            fields_obj = self.pool.get('ir.model.fields')
            field_value = fields_obj.browse(cr, uid, model_object_field, context)
            if field_value.ttype in ['many2one', 'one2many', 'many2many']:
                res_ids = self.pool.get('ir.model').search(cr, uid, [('model', '=', field_value.relation)], context=context)
                sub_field_value = False
                if sub_model_object_field:
                    sub_field_value = fields_obj.browse(cr, uid, sub_model_object_field, context)
                if res_ids:
                    result.update({
                        'sub_object': res_ids[0],
                        'copyvalue': self.build_expression(field_value.name, sub_field_value and sub_field_value.name or False, null_value or False),
                        'sub_model_object_field': sub_model_object_field or False,
                        'null_value': null_value or False
                        })
            else:
                result.update({
                        'copyvalue': self.build_expression(field_value.name, False, null_value or False),
                        'null_value': null_value or False
                        })
        return {'value': result}

    @api.v7
    def build_expression(self, field_name, sub_field_name, null_value):
        """Returns a placeholder expression for use in a template field,
           based on the values provided in the placeholder assistant.

          :param field_name: main field name
          :param sub_field_name: sub field name (M2O)
          :param null_value: default value if the target value is empty
          :return: final placeholder expression
        """
        expression = ''
        if field_name:
            expression = "${object." + field_name
            if sub_field_name:
                expression += "." + sub_field_name
            if null_value:
                expression += " or '''%s'''" % null_value
            expression += "}"
        return expression
