# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FinnMessageError(models.TransientModel):
    _name = 'finn.message.error'

    body = fields.Char()