# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
from odoo.tools.translate import _
from odoo.exceptions import UserError
import datetime

class Simpanan(models.Model):
    _name = 'ksp.simpanan'

    name = fields.Char(string='No. Transaksi', copy=False, index=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', 'Nasabah')
    simpanan_ids = fields.One2many('ksp.simpanan.detail', 'simpanan_id', string='Simpanan')
    amount_total = fields.Float(compute='_compute_total', string='Total', store=True)
    wajib_id = fields.Float(compute='_compute_wajib', string='Simpanan Wajib', store=True)
    sukarela_id = fields.Float(compute='_compute_sukarela', string='Simpanan Sukarela', store=True)
    pokok_id = fields.Float(compute='_compute_pokok', string='Simpanan Pokok', default=25000, store=True)
    tanggal = fields.Date(string='Tanggal Pembuatan', default=fields.Date.today())
    pekerjaan = fields.Selection([("it", "IT"), ("dr", "Delivery")], string='Pekerjaan')

    @api.depends('simpanan_ids')
    def _compute_total(self):
        for doc in self:
            amount_total = sum(doc.simpanan_ids.mapped('total'))
            doc.amount_total = amount_total

    @api.depends('simpanan_ids')
    def _compute_wajib(self):
        for doc in self:
            amount_total = sum(doc.simpanan_ids.mapped('simpanan_wajib'))
            doc.wajib_id = amount_total

    @api.depends('simpanan_ids')
    def _compute_sukarela(self):
        for doc in self:
            amount_total = sum(doc.simpanan_ids.mapped('simpanan_sukarela'))
            doc.sukarela_id = amount_total

    @api.depends('simpanan_ids')
    def _compute_pokok(self):
        for doc in self:
            amount_total = sum(doc.simpanan_ids.mapped('simpanan_pokok'))
            doc.pokok_id = amount_total


class SimpananDetail(models.Model):
    _name = 'ksp.simpanan.detail'
    simpanan_id = fields.Many2one('ksp.simpanan', string='Simpanan')
    tanggal_simpan = fields.Date(string='Tanggal', default=fields.Date.today())
    simpanan_wajib = fields.Float(string='Wajib')
    simpanan_sukarela = fields.Float(string='Sukarela')
    simpanan_pokok = fields.Float(string='Pokok')
    total = fields.Float(string='Total', compute='_get_total', store=True)

    @api.depends('simpanan_wajib', 'simpanan_sukarela', 'simpanan_pokok')
    def _get_total(self):
        for doc in self:
            doc.total = doc.simpanan_wajib + doc.simpanan_sukarela + doc.simpanan_pokok


class SimpananReport(models.Model):
    _name = "simpanan.report"
    _auto = False

    partner_id = fields.Many2one('res.partner', string='Nasabah')
    wajib_id = fields.Float(string='Simpanan Wajib')
    sukarela_id = fields.Float(string='Simpanan Sukarela')
    pokok_id = fields.Float(string='Simpanan Pokok')
    amount_total = fields.Float(string='Total')
    tanggal = fields.Date(string='Tanggal Pembuatan')

    @api.model
    def init(self):
        tools.drop_view_if_exists(self._cr, 'simpanan_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW simpanan_report AS (
                SELECT
                    MIN(ol.id) AS id,
                    ol.partner_id AS partner_id,
                    ol.wajib_id AS wajib_id,
                    ol.sukarela_id AS sukarela_id,
                    ol.pokok_id AS pokok_id,
                    ol.amount_total AS amount_total,
                    ol.tanggal AS tanggal
                FROM ksp_simpanan ol
                GROUP BY
                    ol.partner_id,
                    ol.wajib_id,
                    ol.sukarela_id,
                    ol.pokok_id,
                    ol.amount_total,
                    ol.tanggal
            )
        """)