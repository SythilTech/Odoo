# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import functools
from werkzeug import urls
from datetime import datetime
import base64

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

class VoipCallTemplate(models.Model):

    _name = "voip.call.template"

    name = fields.Char(string="Name")
    model_id = fields.Many2one('ir.model', string="Applies to", help="The kind of document with with this template can be used")
    voip_account_id = fields.Many2one('voip.account', string="VOIP Account")
    to_address = fields.Char(string="To Address", help="Use placeholders")
    media_id = fields.Many2one('voip.media', string="Media")
    codec_id = fields.Many2one('voip.codec', string="Codec")
    call_dialog_id = fields.Many2one('voip.dialog', string="Call Dialog")
    type = fields.Selection([('prerecorded','Pre Recorded')], string="Template Type", default="prerecorded")
    model_object_field_id = fields.Many2one('ir.model.fields', string="Field", help="Select target field from the related document model.\nIf it is a relationship field you will be able to select a target field at the destination of the relationship.")
    sub_object_id = fields.Many2one('ir.model', string='Sub-model', readonly=True, help="When a relationship field is selected as first field, this field shows the document model the relationship goes to.")
    sub_model_object_field_id = fields.Many2one('ir.model.fields', string='Sub-field', help="When a relationship field is selected as first field, this field lets you select the target field within the destination document model (sub-model).")
    null_value = fields.Char(string='Default Value', help="Optional value to use if the target field is empty")
    copyvalue = fields.Char(string='Placeholder Expression', help="Final placeholder expression, to be copy-pasted in the desired template field.")

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
        
    def make_call(self, record_id):
        _logger.error("Make Call")
        to_address = self.render_template(self.to_address, self.model_id.model, record_id)
        self.voip_account_id.make_call(to_address, self.call_dialog_id, self.model_id.model, record_id)

    def render_template(self, template_txt, model, res_id):
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
        try:
            mako_env = mako_safe_template_env if self.env.context.get('safe') else mako_template_env
            template = mako_template_env.from_string(tools.ustr(template_txt))
        except Exception:
            _logger.error("Failed to load template %r", template)
            return False

        # prepare template variables
        user = self.env.user
        record = self.env[model].browse( int(res_id) )

        variables = {
            'user': user
        }

        variables['object'] = record

        try:
            render_result = template.render(variables)
        except Exception as e:
            _logger.error("Failed to render template %r using values %r" % (template, variables))
            _logger.error(e)
            render_result = u""
        if render_result == u"False":
            render_result = u""

        return render_result