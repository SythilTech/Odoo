# -*- coding: utf-8 -*-

import requests
import json
import base64
from datetime import datetime
import functools
from werkzeug import urls
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models, tools

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

class IntegrationManyChatServer(models.Model):

    _name = 'integration.manychat.server'

    name = fields.Char(string="Name", help="Human meaningful name to describe the Dynamic Content Server", required=True)
    server_slug = fields.Char(string="Slug", help="Name in url", required=True)
    model_id = fields.Many2one('ir.model', string="Model", help="Reads Data from this model", required=True)
    model_name = fields.Char(related="model_id.model", string="Model Name")
    domain = fields.Char(string="Domain", help="Returns only records that match the domain", required=True)
    message_ids = fields.One2many('integration.manychat.server.message', 'server_id', string="Messages")

class IntegrationManyChatServerMessage(models.Model):

    _name = 'integration.manychat.server.message'
    
    server_id = fields.Many2one('integration.manychat.server', string="Server")
    type = fields.Selection([('text', 'Text')], string="Type", required=True)
    text = fields.Text(string="Text", help="Use Dynamic Placeholders")

    def render_message(self, template, model, res_id):
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

        template = mako_template_env.from_string(tools.ustr(template))

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