# -*- coding: utf-8 -*-
from datetime import datetime
import functools
from werkzeug import urls
import logging
_logger = logging.getLogger(__name__)

from openerp import api, fields, models, tools

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
        'quote': urls.url_quote,
        'urlencode': urls.url_encode,
        'datetime': datetime,
        'len': len,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'filter': filter,
        'reduce': functools.reduce,
        'map': map,
        'round': round,
        
        # dateutil.relativedelta is an old-style class and cannot be directly
        # instanciated wihtin a jinja2 expression, so a lambda "proxy" is
        # is needed, apparently.
        'relativedelta': lambda *a, **kw : relativedelta.relativedelta(*a, **kw),
    })
except ImportError:
    _logger.warning("jinja2 not available, templating features will not work!")


class SmsTemplate(models.Model):

    _name = "sms.template"
    
    name = fields.Char(required=True, string='Template Name', translate=True)
    model_id = fields.Many2one('ir.model', string='Applies to', help="The kind of document with with this template can be used")
    model = fields.Char(related="model_id.model", string='Related Document Model', store=True, readonly=True)
    template_body = fields.Text('Body', translate=True, help="Plain text version of the message (placeholders may be used here)")
    sms_from = fields.Char(string='From (Mobile)', help="Sender mobile number (placeholders may be used here). If not set, the default value will be the author's mobile number.")
    sms_to = fields.Char(string='To (Mobile)', help="To mobile number (placeholders may be used here)")
    account_gateway_id = fields.Many2one('sms.account', string="Account")    
    model_object_field_id = fields.Many2one('ir.model.fields', string="Field", help="Select target field from the related document model.\nIf it is a relationship field you will be able to select a target field at the destination of the relationship.")
    sub_object_id = fields.Many2one('ir.model', string='Sub-model', readonly=True, help="When a relationship field is selected as first field, this field shows the document model the relationship goes to.")
    sub_model_object_field_id = fields.Many2one('ir.model.fields', string='Sub-field', help="When a relationship field is selected as first field, this field lets you select the target field within the destination document model (sub-model).")
    null_value = fields.Char(string='Default Value', help="Optional value to use if the target field is empty")
    copyvalue = fields.Char(string='Placeholder Expression', help="Final placeholder expression, to be copy-pasted in the desired template field.")
    lang = fields.Char(string='Language', help="Optional translation language (ISO code) to select when sending out an email. If not set, the english version will be used. This should usually be a placeholder expression that provides the appropriate language, e.g. ${object.partner_id.lang}.", placeholder="${object.partner_id.lang}")
    from_mobile_verified_id = fields.Many2one('sms.number', string="From Mobile (stored)")
    from_mobile = fields.Char(string="From Mobile", help="Placeholders are allowed here")
    media_id = fields.Binary(string="Media(MMS)")
    media_filename = fields.Char(string="Media Filename")    
    media_ids = fields.Many2many('ir.attachment', string="Media(MMS)[Automated Actions Only]")
    
    @api.onchange('model_object_field_id')
    def _onchange_model_object_field_id(self):
        if self.model_object_field_id.relation:
            self.sub_object_id = self.env['ir.model'].search([('model','=',self.model_object_field_id.relation)])[0].id
        else:
            self.sub_object_id = False    
    
        if self.model_object_field_id:
            self.copyvalue = self.build_expression(self.model_object_field_id.name, self.sub_model_object_field_id.name, self.null_value)

    @api.onchange('sub_model_object_field_id')
    def _onchange_sub_model_object_field_id(self):
        if self.sub_model_object_field_id:
            self.copyvalue = self.build_expression(self.model_object_field_id.name, self.sub_model_object_field_id.name, self.null_value)
    
    @api.onchange('from_mobile_verified_id')
    def _onchange_from_mobile_verified_id(self):
        if self.from_mobile_verified_id:
            self.from_mobile = self.from_mobile_verified_id.mobile_number
    
    @api.model
    def send_sms(self, template_id, record_id):
        """Send the sms using all the details in this sms template, using the specified record ID""" 
        sms_template = self.env['sms.template'].browse( int(template_id) )
        
        rendered_sms_template_body = self.env['sms.template'].render_template(sms_template.template_body, sms_template.model_id.model, record_id)
        
        rendered_sms_to = self.env['sms.template'].render_template(sms_template.sms_to, sms_template.model_id.model, record_id)
         
        gateway_model = sms_template.from_mobile_verified_id.account_id.account_gateway_id.gateway_model_name

        #Queue the SMS message since we can't directly send MMS
        queued_sms = self.env['sms.message'].create({'record_id': record_id,'model_id': sms_template.model_id.id,'account_id':sms_template.from_mobile_verified_id.account_id.id,'from_mobile':sms_template.from_mobile,'to_mobile':rendered_sms_to,'sms_content':rendered_sms_template_body, 'direction':'O','message_date':datetime.utcnow(), 'status_code': 'queued'})

        #Also create the MMS attachment
        if sms_template.media_id:
            self.env['ir.attachment'].sudo().create({'name': 'mms ' + str(queued_sms.id), 'type': 'binary', 'datas': sms_template.media_id, 'public': True, 'res_model': 'sms.message', 'res_id': queued_sms.id})

        #Turn the queue manager on
        self.env['ir.model.data'].get_object('sms_frame', 'sms_queue_check').active = True
        
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

    @api.model
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
