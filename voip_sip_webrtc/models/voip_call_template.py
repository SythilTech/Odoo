# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
from urllib import urlencode, quote as quote
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
    
class VoipCallTemplate(models.Model):

    _name = "voip.call.template"

    name = fields.Char(string="Name")
    model_id = fields.Many2one('ir.model', string="Applies to", help="The kind of document with with this template can be used")
    voip_account_id = fields.Many2one('voip.account', string="VOIP Account")
    to_address = fields.Char(string="To Address", help="Use placeholders")
    gsm_media = fields.Binary(string="(OBSOLETE)GSM Audio File")
    media = fields.Binary(string="Raw Audio File")
    codec_id = fields.Many2one('voip.codec', string="Codec")

    def make_call(self, record_id):
        _logger.error("Make Call")
        to_address = self.render_template(self.to_address, self.model_id.model, record_id)
        decoded_media = base64.decodestring(self.media)
        self.voip_account_id.make_call(to_address, decoded_media, self.codec_id, self.model_id.model, record_id)
        
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