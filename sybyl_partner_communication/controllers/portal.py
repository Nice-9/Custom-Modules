
from odoo import http, _
from odoo.http import request
from werkzeug.exceptions import NotFound, Forbidden
from odoo.addons.portal.controllers.mail import _message_post_helper,_check_special_access
from odoo.addons.portal.controllers import mail
from odoo.addons.portal.controllers import portal
from odoo.osv import expression
from odoo.addons.portal.controllers import mail


class PortalChatterUpdate(mail.PortalChatter):
    @http.route('/mail/chatter_fetch', type='json', auth='public', website=True)
    def portal_message_fetch(self, res_model, res_id, domain=False, limit=10, offset=0, **kw):
        if not domain:
            domain = []
        # Only search into website_message_ids, so apply the same domain to perform only one search
        # extract domain from the 'website_message_ids' field
        model = request.env[res_model]
        field = model._fields['website_message_ids']
        field_domain = field.get_domain_list(model)
        domain = expression.AND([
            domain,
            field_domain,
            [('res_id', '=', res_id), '|', ('body', '!=', ''), ('attachment_ids', '!=', False)]
        ])

        # Check access
        Message = request.env['mail.message']
        if kw.get('token'):
            access_as_sudo = _check_special_access(res_model, res_id, token=kw.get('token'))
            if not access_as_sudo:  # if token is not correct, raise Forbidden
                raise Forbidden()
            # Non-employee see only messages with not internal subtype (aka, no internal logs)
            if not request.env['res.users'].has_group('base.group_user'):
                domain = expression.AND([Message._get_search_domain_share(), domain])
        Message = request.env['mail.message'].sudo()
        return {
            'messages': Message.search(domain, limit=limit, offset=offset).portal_message_format(options=kw),
            'message_count': Message.search_count(domain)
        }


def _message_post_helper(res_model, res_id, message, token='', _hash=False, pid=False, nosubscribe=True, **kw):
    record = request.env[res_model].browse(res_id)
    # check if user can post with special token/signed token. The "else" will try to post message with the
    # current user access rights (_mail_post_access use case).
    if token or (_hash and pid):
        pid = int(pid) if pid else False
        if _check_special_access(res_model, res_id, token=token, _hash=_hash, pid=pid):
            record = record.sudo()
        else:
            raise Forbidden()
    else:  # early check on access to avoid useless computation
        if record._name != 'res.partner':
            record.check_access_rights('read')
            record.check_access_rule('read')

    # deduce author of message
    author_id = request.env.user.partner_id.id if request.env.user.partner_id else False
    # Signed Token Case: author_id is forced
    if _hash and pid:
        author_id = pid
    # Token Case: author is document customer (if not logged) or itself even if user has not the access
    elif token:
        if request.env.user._is_public():
            # TODO : After adding the pid and sign_token in access_url when send invoice by email, remove this line
            # TODO : Author must be Public User (to rename to 'Anonymous')
            author_id = record.partner_id.id if hasattr(record, 'partner_id') and record.partner_id.id else author_id
        else:
            if not author_id:
                raise NotFound()

    email_from = None
    if author_id and 'email_from' not in kw:
        partner = request.env['res.partner'].sudo().browse(author_id)
        email_from = partner.email_formatted if partner.email else None

    message_post_args = dict(
        body=message,
        message_type=kw.pop('message_type', "comment"),
        subtype_xmlid=kw.pop('subtype_xmlid', "mail.mt_comment"),
        author_id=author_id,
        **kw
    )
    # This is necessary as mail.message checks the presence
    # of the key to compute its default email from
    if email_from:
        message_post_args['email_from'] = email_from
    if record._name != 'res.partner':
        return record.with_context(mail_create_nosubscribe=nosubscribe).message_post(**message_post_args)
    return record.with_context(mail_create_nosubscribe=nosubscribe).sudo().message_post(**message_post_args)

mail._message_post_helper = _message_post_helper

class CustomerPortalCommunication(portal.CustomerPortal):

    @http.route(['/my/communication'], type='http', auth="user", website=True)
    def portal_my_communication(self, **kwargs):
        values = {}
        values.update({
            'page_name': 'communication'
            })
        values.update({
            'partner_id':request.env.user.partner_id
            })
        return request.render("sybyl_partner_communication.portal_my_communication", values)