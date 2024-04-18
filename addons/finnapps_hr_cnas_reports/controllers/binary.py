from odoo import http
from odoo.http import request
import base64
import io
import os
import mimetypes
from werkzeug.utils import redirect
import logging as log

class Catalogue(http.Controller):

    @http.route('/web/binary/download_employee_file', type='http', auth="public")
    def download_employee_file(self, filename, **kw):
        """ Download link for files stored as binary fields.
        """

     
        # Vérifier si le fichier existe
        attachment = request.env['ir.attachment'].sudo().search_read(
            [('name', '=', filename)],
            ["name", "datas", "mimetype"]
        )
        log.warning('attach ::::::')
        log.warning(attachment)

        if attachment:
            log.warning('in if ')

            attachment = attachment[0]
            log.warning(attachment)
        else:
            return request.not_found()

        if attachment["datas"]:
            data = io.BytesIO(base64.standard_b64decode(attachment["datas"]))
            extension = os.path.splitext(attachment["name"] or '')[1]
            extension = extension if extension else mimetypes.guess_extension(attachment["mimetype"] or '')
            filename = attachment['name']
            filename = filename if os.path.splitext(filename)[1] else filename + extension
            return http.send_file(data, filename=filename, as_attachment=True)
        else:
            return request.not_found()


    @http.route('/web/binary/download_company_file', type='http', auth="public")
    def download_company_file(self, filename, **kw):
        """ Download link for files stored as binary fields.
        """

     
        # Vérifier si le fichier existe
        attachment = request.env['ir.attachment'].sudo().search_read(
            [('name', '=', filename)],
            ["name", "datas", "mimetype"]
        )

        if attachment:
            attachment = attachment[0]
        else:
            return request.not_found()

        if attachment["datas"]:
            data = io.BytesIO(base64.standard_b64decode(attachment["datas"]))
            extension = os.path.splitext(attachment["name"] or '')[1]
            extension = extension if extension else mimetypes.guess_extension(attachment["mimetype"] or '')
            filename = attachment['name']
            filename = filename if os.path.splitext(filename)[1] else filename + extension
            return http.send_file(data, filename=filename, as_attachment=True)
        else:
            return request.not_found()

