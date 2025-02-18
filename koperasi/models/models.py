# -*- coding: utf-8 -*-
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'
from odoo import models, fields, api, tools
from odoo.tools.translate import _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta as rd
import random
import datetime


def rounding(arg1, arg2, arg3):
    if arg1 % arg2 > arg3:
        result = arg1 + (arg2 - arg1 % arg2)
    else:
        result = arg1 + (arg3 - arg1 % arg2)
    return result


class Kredit(models.Model):
    _name = 'ksp.kredit'
    
    name = fields.Char('Name', default='Draft')
    kredit_type = fields.Many2one('ksp.kredit.type', 'Jenis Kredit', store=True)
    tanggal = fields.Date('Tanggal', default=fields.Date.today(), store=True)
    tgl_cair = fields.Date('Tanggal Cair', default=fields.Date.today(), store=True)
    account_cair = fields.Many2one('account.account', 'Metode Pencairan')
    partner_id = fields.Many2one('res.partner', 'Nasabah', store=True)
    pokok = fields.Integer('Pokok', default=0, store=True)
    bunga = fields.Integer('Bunga', default=0, compute='_compute_bunga', store=True)
    tempo = fields.Integer('Jangka waktu', default=1, store=True)
    tempo_type = fields.Selection([('T', 'Tahun'), ('B', 'Bulan')], default='B')
    angsuran = fields.Integer('Angsuran', compute='_compute_angsuran', store=True)
    rate = fields.Float('Suku Bunga per bulan', default=1.5, store=True)
    rate_tempo = fields.Selection([('B', 'Bulan'), ('T', 'Tahun')])
    rate_type = fields.Selection([
        ('F', 'Flat'),
        ('M', 'Flat Menurun'),
        ('A', 'Anuitet'),
        ('E', 'Efektif'),
        ('K', 'Kontrak')
    ], default='F')
    kredit_line = fields.One2many('ksp.kredit.line', 'kredit_id')
    biaya_line = fields.One2many('ksp.kredit.biaya.line', 'kredit_id')
    move_line = fields.One2many('account.move', 'kredit_id')
    jaminan_line = fields.One2many('ksp.kredit.jaminan.line', 'kredit_id')
    total_angsuran = fields.Integer('Total Angsuran', compute='_compute_total_angsuran')
    total_pokok = fields.Integer('Total Pokok', compute='_compute_total_angsuran')
    total_bunga = fields.Integer('Total Bunga', compute='_compute_total_angsuran')
    sisa_angsuran = fields.Integer('Sisa Angsuran')
    sisa_pokok = fields.Integer('Sisa Pokok')
    sisa_bunga = fields.Integer('Sisa Bunga')
    bulat = fields.Boolean('Pembulatan', default=False)
    apply_1 = fields.Char('Apply 1')
    apply_2 = fields.Char('Apply 2')
    apply_to = fields.Datetime('Apply Timeout')
    apply_key = fields.Char('Key')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Pengajuan'),
        ('validate', 'Disetujui'),
        ('cair', 'Pencairan'),
        ('lunas', 'Lunas'),
        ('macet', 'Bermasalah'),
    ], default='draft')

    def set_bayar(self):
        bayar = self.env['ksp.kredit.bayar'].search([('kredit_id', '=', self.id)])
        action = self.env.ref('trijaya.ksp_kredit_bayar_action_window').read()[0]
        action['context'] = {'default_kredit_id': self.id}
        if self.status != "cair":
            raise UserError(_('Belum Bisa membayar angsuran, silahkan selesaikan proses pencairan'))
        if len(bayar) > 1:
            raise UserError(_('Data pembayaran angsuran double, pastikan hanya ada 1 data'))
        elif len(bayar) == 1:
            action['views'] = [(self.env.ref('trijaya.ksp_kredit_bayar_form_view').id, 'form')]
            action['res_id'] = bayar.ids[0]
        else:
            action['domain'] = [('id', 'in', bayar.ids)]
        return action

    @api.depends('kredit_line')
    def _compute_bunga(self):
        self.bunga = sum(bayar.bunga for bayar in self.kredit_line)

    @api.depends('pokok', 'rate', 'rate_type', 'tempo')
    def _compute_angsuran(self):
        if self.rate_type in ["F", "M"]:
            self.bunga = self.pokok * (self.rate / 100) * self.tempo
            self.angsuran = (self.pokok + self.bunga) / self.tempo
            if self.bulat:
                self.angsuran = rounding(self.angsuran, 1000, 500)
        elif self.rate_type == "E":
            angsur = self.tempo + 1
            tot_angsuran = 0
            self.angsuran = (self.pokok / self.tempo) + ((self.pokok - ((1 - 1) * (self.pokok / self.tempo))) * (self.rate / 100))
            for x in range(1, angsur):
                tot_angsuran += (self.pokok / self.tempo) + ((self.pokok - ((x - 1) * (self.pokok / self.tempo))) * (self.rate / 100))
            self.bunga = tot_angsuran - self.pokok
        elif self.rate_type == "A":
            self.angsuran = self.pokok * ((self.rate / 100) / (1 - (1 + (self.rate / 100)) ** (self.tempo * -1)))
            tot_angsuran = self.angsuran * self.tempo
            self.bunga = tot_angsuran - self.pokok
        else:
            self.angsuran = 99999

    @api.depends('apply_1')
    def generate_apply(self):
        self.apply_1 = str(int(random.random() * 100000000))
        datenow = datetime.datetime.now() + rd(hours=-7) + rd(minutes=15)
        self.apply_to = datenow.strftime(DATETIME_FORMAT)
        key = datetime.datetime.now().strftime('%d%m%Y')
        key2 = sum(int(x) for x in key)
        key3 = ''
        for item in self.apply_1:
            key3 += str((int(item) * key2) % 10)
        self.apply_key = key3

    @api.depends('pokok', 'rate', 'rate_type', 'tempo', 'kredit_line')
    def generate_angsuran(self):
        angsur_total = angsur_bunga = angsur_pokok = 0
        angsur = self.tempo + 1
        tot_bunga = tot_pokok = 0
        krd_id = self.id
        self.env.cr.execute('DELETE FROM ksp_kredit_line WHERE kredit_id = %s' % krd_id)
        if self.rate_type == 'F':
            angsur_total = self.angsuran
            angsur_pokok = self.pokok / self.tempo
            angsur_bunga = angsur_total - angsur_pokok
            for x in range(1, angsur):
                self.kredit_line.create({
                    'kredit_id': self.id,
                    'sequence': x,
                    'angsuran': self.angsuran,
                    'pokok': angsur_pokok,
                    'bunga': angsur_bunga,
                    'sisa_pokok': angsur_pokok,
                    'sisa_bunga': angsur_bunga,
                    'sisa_angsuran': angsur_total,
                })
        elif self.rate_type == 'M':
            pembagi = 1.0 / (sum(x for x in range(1, angsur)))
            angsuran = angsur_total = self.angsuran
            for x in range(1, angsur):
                if self.pokok > self.bunga:
                    angsur_bunga = (self.pokok * (self.rate / 100) * self.tempo) * (pembagi * (angsur - x))
                    angsur_pokok = angsur_total - angsur_bunga
                else:
                    angsur_pokok = self.pokok * (pembagi * x)
                    angsur_bunga = angsur_total - angsur_pokok
                tot_bunga += angsur_bunga
                tot_pokok += angsur_pokok
                if x == (angsur - 1):
                    if tot_pokok > self.pokok:
                        angsur_pokok -= (tot_pokok - self.pokok)
                    elif tot_pokok < self.pokok:
                        angsur_pokok += (self.pokok - tot_pokok)
                    angsuran = angsur_pokok + angsur_bunga
                if x == (angsur - 1):
                    if tot_bunga > self.bunga:
                        angsur_bunga -= (tot_bunga - self.bunga)
                    elif tot_bunga < self.bunga:
                        angsur_bunga += (self.bunga - tot_bunga)
                    angsuran = angsur_pokok + angsur_bunga
                self.kredit_line.create({
                    'kredit_id': self.id,
                    'sequence': x,
                    'angsuran': angsuran,
                    'pokok': angsur_pokok,
                    'bunga': angsur_bunga,
                    'sisa_pokok': angsur_pokok,
                    'sisa_bunga': angsur_bunga,
                    'sisa_angsuran': angsur_total,
                })
        elif self.rate_type == "E":
            angsur_pokok = self.pokok / self.tempo
            for x in range(1, angsur):
                angsuran = (self.pokok / self.tempo) + ((self.pokok - ((x - 1) * (self.pokok / self.tempo))) * (self.rate / 100))
                angsur_bunga = angsuran - angsur_pokok
                tot_bunga += angsur_bunga
                tot_pokok += angsur_pokok
                if x == (angsur - 1):
                    if tot_pokok > self.pokok:
                        angsur_pokok -= (tot_pokok - self.pokok)
                    elif tot_pokok < self.pokok:
                        angsur_pokok += (self.pokok - tot_pokok)
                    angsuran = angsur_pokok + angsur_bunga
                if x == (angsur - 1):
                    if tot_bunga > self.bunga:
                        angsur_bunga -= (tot_bunga - self.bunga)
                    elif tot_bunga < self.bunga:
                        angsur_bunga += (self.bunga - tot_bunga)
                    angsuran = angsur_pokok + angsur_bunga
                self.kredit_line.create({
                    'kredit_id': self.id,
                    'sequence': x,
                    'angsuran': angsuran,
                    'pokok': angsur_pokok,
                    'bunga': angsur_bunga,
                    'sisa_pokok': angsur_pokok,
                    'sisa_bunga': angsur_bunga,
                    'sisa_angsuran': angsur_total,
                })
        elif self.rate_type == 'A':
            angsuran = self.pokok * ((self.rate / 100) / (1 - (1 + (self.rate / 100)) ** (self.tempo * -1)))
            sisa_pokok = self.pokok
            denda = 0
            for x in range(1, angsur):
                angsur_bunga = sisa_pokok * (self.rate / 100)
                angsur_pokok = angsuran - angsur_bunga
                tot_bunga += angsur_bunga
                tot_pokok += angsur_pokok
                sisa_pokok -= angsur_pokok
                if x == (angsur - 1):
                    if tot_pokok > self.pokok:
                        angsur_pokok -= (tot_pokok - self.pokok)
                        denda = 9999
                    elif tot_pokok < self.pokok:
                        denda = self.pokok - tot_pokok
                        angsur_pokok += (self.pokok - tot_pokok)
                    angsuran = angsur_pokok + angsur_bunga
                if x == (angsur - 1):
                    if tot_bunga > self.bunga:
                        angsur_bunga -= (tot_bunga - self.bunga)
                    elif tot_bunga < self.bunga:
                        angsur_bunga += (self.bunga - tot_bunga)
                    angsuran = angsur_pokok + angsur_bunga
                self.kredit_line.create({
                    'kredit_id': self.id,
                    'sequence': x,
                    'angsuran': angsuran,
                    'pokok': angsur_pokok,
                    'bunga': angsur_bunga,
                    'denda': denda,
                    'sisa_pokok': angsur_pokok,
                    'sisa_bunga': angsur_bunga,
                    'sisa_angsuran': angsur_total,
                })
        else:
            angsur_bunga = self.pokok * (self.rate / 100) * self.tempo
            self.sisa_angsuran = self.sisa_pokok = self.sisa_bunga = 0
            for x in range(1, angsur):
                angsur_pokok = 0
                angsur_total = angsur_pokok + angsur_bunga
                if x == (angsur - 1):
                    angsur_pokok = self.pokok
                    angsur_total = angsur_pokok + angsur_bunga
                self.sisa_angsuran += angsur_total
                self.sisa_pokok += angsur_pokok
                self.sisa_bunga += angsur_bunga
                self.kredit_line.create({
                    'kredit_id': self.id,
                    'sequence': x,
                    'angsuran': angsur_total,
                    'pokok': angsur_pokok,
                    'bunga': angsur_bunga,
                    'sisa_pokok': angsur_pokok,
                    'sisa_bunga': angsur_bunga,
                    'sisa_angsuran': angsur_total,
                })
        self.env.cr.execute('DELETE FROM ksp_kredit_biaya_line WHERE kredit_id = %s' % krd_id)
        for x in self.kredit_type.kredit_line:
            nominal = ((x.rate / 100) * self.pokok) + x.nominal
            self.name = str(self.pokok) + x.account_id.name
            self.biaya_line.create({
                'kredit_id': self.id,
                'account_id': x.account_id.id,
                'nominal': nominal
            })

    @api.depends('kredit_line.angsuran', 'kredit_line.pokok', 'kredit_line.bunga')
    def _compute_total_angsuran(self):
        self.total_angsuran = self.total_bunga = self.total_pokok = 0
        self.sisa_angsuran = self.sisa_bunga = self.sisa_pokok = 0
        for line in self.kredit_line:
            self.total_angsuran += line.angsuran
            self.total_pokok += line.pokok
            self.total_bunga += line.bunga
            if not line.lunas:
                self.sisa_angsuran += line.angsuran
                self.sisa_pokok += line.pokok
                self.sisa_bunga += line.bunga

    def confirm_kredit(self):
        self.status = 'confirm'

    def validasi_kredit(self):
        to = fields.Datetime.from_string(self.apply_to)
        sekarang = datetime.datetime.now() + rd(hours=-7)
        if self.apply_2 == self.apply_key:
            self.status = 'validate'
        else:
            if to < sekarang:
                raise UserError(_('Tidak dapat divalidasi, token kadaluwarsa, silahkan generate token baru-2'))
            else:
                raise UserError(_('Tidak dapat divalidasi, kode apply 2 salah'))

    def pencairan_kredit(self):
        pokok = self.pokok * 1.0
        total_biaya = sum(biaya.nominal for biaya in self.biaya_line)
        if not self.account_cair.id:
            raise UserError(_('Metode Pencairan tidak boleh kosong'))
        else:
            self.status = 'cair'
            self.tgl_cair = fields.Date.today()
            tgl_cair = fields.Date.from_string(self.tgl_cair)
            for item in self.kredit_line:
                tgl_jt = tgl_cair + rd(months=item.sequence)
                item.tgl_jt = tgl_jt.strftime(DATE_FORMAT)

    def pelunasan_kredit(self):
        self.status = 'lunas'

    def kredit_macet(self):
        self.status = 'macet'

    def button_cancel(self):
        if self.status in ['lunas', 'macet']:
            self.status = 'cair'
        elif self.status == 'cair':
            self.status = 'validate'
        elif self.status == 'validate':
            self.status = 'confirm'
        else:
            self.status = 'draft'

class KreditLine(models.Model):
    _name = 'ksp.kredit.line'
    _order = 'kredit_id, sequence'

    name = fields.Char('Name', compute='loop_angsuran')
    sequence = fields.Integer('No. Urut', default=0)
    kredit_id = fields.Many2one('ksp.kredit')
    bayar_line = fields.One2many('ksp.kredit.line.bayar', 'kredit_line_id')
    tgl_jt = fields.Date('Tanggal Jatuh Tempo')
    tgl_bayar = fields.Date('Tanggal Lunas', default=fields.Date.today())
    angsuran = fields.Integer('Angsuran', default=0)
    pokok = fields.Integer('Pokok', default=0)
    bunga = fields.Integer('Bunga', default=0)
    denda = fields.Integer('Denda', compute='_hitung_denda')
    lunas = fields.Boolean('Lunas')
    sisa_pokok = fields.Integer('Sisa Pokok', compute='_hitung_bayar')
    sisa_bunga = fields.Integer('Sisa Bunga', compute='_hitung_bayar')
    sisa_angsuran = fields.Integer('Sisa Angsuran', compute='_hitung_bayar')
    pembayaran = fields.Integer('Total Pembayaran', compute='_hitung_bayar')
    is_denda = fields.Boolean('Tanpa Denda')

    def set_bayar(self):
        bayar = self.env['ksp.kredit.bayar'].search([('kredit_id', '=', self.id)])
        action = self.env.ref('trijaya.ksp_kredit_bayar_action_window').read()[0]
        action['context'] = {'default_kredit_id': self.id}
        if len(bayar) > 1:
            raise UserError(_('Data pembayaran angsuran double, pastikan hanya ada 1 data'))
        elif len(bayar) == 1:
            action['views'] = [(self.env.ref('trijaya.ksp_kredit_bayar_form_view').id, 'form')]
            action['res_id'] = bayar.ids[0]
        else:
            action['domain'] = [('id', 'in', bayar.ids)]
        return action

    @api.depends('name')
    def loop_angsuran(self):
        default = 0
        for doc in self:
            default += 1
            doc.name = "Angsuran " + str(default)

    @api.depends('tgl_jt')
    def _hitung_denda(self):
        today = fields.Date.today()
        for record in self:
            if record.tgl_jt:
                jtempo = fields.Date.from_string(record.tgl_jt)
                if jtempo < today:
                    selisih = today - jtempo
                    record.denda = record.kredit_id.kredit_type.denda * selisih.days
                else:
                    record.denda = 0
            else:
                record.denda = 0

    @api.depends('bayar_line.nominal', 'angsuran', 'bunga', 'pokok')
    def _hitung_bayar(self):
        for record in self:
            record.pembayaran = sum(bayar.nominal for bayar in record.bayar_line)
            record.sisa_angsuran = record.angsuran - record.pembayaran
            if record.sisa_angsuran > 0:
                if record.pembayaran <= record.bunga:
                    record.sisa_bunga = record.bunga - record.pembayaran
                    record.sisa_pokok = record.pokok
                else:
                    record.sisa_bunga = 0
                    record.sisa_pokok = record.pokok - (record.pembayaran - record.bunga)
            else:
                record.lunas = True

class KreditJaminanLine(models.Model):
    _name = 'ksp.kredit.jaminan.line'

    name = fields.Char('name')
    kredit_id = fields.Many2one('ksp.kredit', 'Kredit Id')
    jaminan_id = fields.Many2one('ksp.jaminan', 'Jaminan id')
    nilai = fields.Integer('Nilai', compute='_get_nilai')

    @api.depends('jaminan_id')
    def _get_nilai(self):
        for record in self:
            record.nilai = record.jaminan_id.harga_taksiran

class KreditBayar(models.Model):
    _name = 'ksp.kredit.bayar'
    _rec_name = 'kredit_id'

    name = fields.Char('No. Kwitansi', default='Draft')
    kredit_id = fields.Many2one('ksp.kredit', 'No. Pinjaman')
    partner_id = fields.Many2one('res.partner', string='Nasabah', track_visibility='onchange', related='kredit_id.partner_id')
    account_id = fields.Many2one('account.account', 'Metode Pembayaran')
    date = fields.Date('Tanggal Bayar', default=fields.Date.today())
    bayar_line = fields.One2many('ksp.kredit.line.bayar', 'bayar_id')
    amount = fields.Integer('Nominal Pembayaran', default=0)
    total_paid = fields.Integer(compute='_hitung_bayar')
    user_id = fields.Many2one('res.users', 'operator')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('post', 'Posting')
    ], default='draft')

    @api.depends('bayar_line.nominal')
    def _hitung_bayar(self):
        for record in self:
            record.total_paid = sum(line.nominal for line in record.bayar_line)

    def confirm_bayar(self):
        for record in self:
            if record.total_paid != record.amount:
                raise UserError(_('Tidak dapat diconfirm, total pembayaran dan total detail tidak sama'))
            else:
                record.state = 'confirm'

    def post_bayar(self):
        for record in self:
            record.state = 'post'

    def cancel_bayar(self):
        for record in self:
            if record.state == 'post':
                record.state = 'confirm'
            elif record.state == 'confirm':
                record.state = 'draft'

class KreditLineBayar(models.Model):
    _name = 'ksp.kredit.line.bayar'

    name = fields.Char()
    kredit_id = fields.Integer(compute='_get_kredit_id')
    kredit_line_id = fields.Many2one('ksp.kredit.line')
    bayar_id = fields.Many2one('ksp.kredit.bayar')
    angsur_id = fields.Many2one('ksp.kredit.line')
    tgl_bayar = fields.Date('Tanggal Bayar', related='bayar_id.date', store=True, default=fields.Date.today())
    nominal = fields.Integer('Nominal', default=0)
    user_id = fields.Many2one('res.users', 'operator')

    @api.depends('bayar_id.kredit_id')
    def _get_kredit_id(self):
        for record in self:
            record.kredit_id = record.bayar_id.kredit_id.id

class KreditBiayaLine(models.Model):
    _name = 'ksp.kredit.biaya.line'

    name = fields.Char()
    kredit_id = fields.Many2one('ksp.kredit')
    account_id = fields.Many2one('account.account')
    nominal = fields.Integer('Nominal', default=0)

class KreditType(models.Model):
    _name = 'ksp.kredit.type'

    name = fields.Char()
    account_pokok = fields.Many2one('account.account', 'Akun Pokok')
    account_bunga = fields.Many2one('account.account', 'Akun Bunga')
    account_denda = fields.Many2one('account.account', 'Akun Denda')
    denda = fields.Integer('Nominal denda per hari')
    kredit_line = fields.One2many('ksp.kredit.type.line', 'kredit_id')
    seq_id = fields.Many2one('ir.sequence', 'Sequence Id')
    journal_cair = fields.Many2one('account.journal', 'Journal Pencairan')
    journal_angsur = fields.Many2one('account.journal', 'Journal Bayar Angsuran')

class KreditTypeLine(models.Model):
    _name = 'ksp.kredit.type.line'

    name = fields.Char()
    kredit_id = fields.Many2one('ksp.kredit')
    account_id = fields.Many2one('account.account')
    rate = fields.Float('Persentase -> Pokok Pinjaman', default=0.0)
    nominal = fields.Integer('Nominal', default=0)

class AccountMove(models.Model):
    _inherit = 'account.move'

    kredit_id = fields.Many2one('ksp.kredit')

class ResPartner(models.Model):
    _inherit = 'res.partner'

    kredit = fields.Boolean('Nasabah Kredit')
    deposito = fields.Boolean('Nasabah Deposito')
    tabungan = fields.Boolean('Nasabah Tabungan')
    no_id = fields.Char('N.I.K')

class KspJaminan(models.Model):
    _name = 'ksp.jaminan'

    name = fields.Char('Name')
    description = fields.Char('Deskripsi')
    image = fields.Binary("Image", attachment=True, help="This field holds the image used as avatar for this contact, limited to 1024x1024px")
    image2 = fields.Binary("Image2", attachment=True, help="This field holds the image used as avatar for this contact, limited to 1024x1024px")
    image3 = fields.Binary("Image3", attachment=True, help="This field holds the image used as avatar for this contact, limited to 1024x1024px")
    image4 = fields.Binary("Image4", attachment=True, help="This field holds the image used as avatar for this contact, limited to 1024x1024px")
    jenis = fields.Selection([
        ('mobil', 'Mobil'),
        ('motor', "Sepeda Motor"),
        ('sertifikat', 'Sertifikat'),
        ('other', 'Lain-lain'),
    ])
    merk = fields.Many2one("ksp.jaminan.merk", "Merk")
    model = fields.Many2one("ksp.jaminan.model", "Model")
    harga_pasar = fields.Integer("Harga Pasar", compute="_get_harga_pasar")
    harga_taksiran = fields.Integer("Harga Taksiran", help="Nilai jaminan sesuai dengan kondisi jaminan")
    type = fields.Char("Type", help="Diisi sesuai tipe di STNK")
    no_mesin = fields.Char("No. Mesin")
    no_rangka = fields.Char("No. Rangka")
    no_polisi = fields.Char("No. Polisi")
    no_bpkb = fields.Char("No. BPKB")
    tahun = fields.Char("Tahun")
    warna = fields.Char("Warna")
    nama_stnk = fields.Char("Atas Nama STNK")
    alamat_stnk = fields.Char("Alamat STNK")
    no_sertifikat = fields.Char('Nomor Sertifikat')
    bentuk_sertifikat = fields.Char('Bentuk Sertifikat')
    alamat_sertifikat = fields.Char('Alamat')
    luas_sertifikat = fields.Char('Luas Tanah/Bangunan')
    no_surat_ukur = fields.Char('No. Surat Ukur')
    tgl_surat_ukur = fields.Char('Tanggal Surat Ukur')
    keterangan = fields.Text('Keterangan')

    @api.depends('model')
    def _get_harga_pasar(self):
        for record in self:
            record.harga_pasar = record.model.harga_pasar

class KspJaminanMerk(models.Model):
    _name = "ksp.jaminan.merk"

    name = fields.Char('Nama')
    image = fields.Binary("Image", attachment=True, help="This field holds the image used as avatar for this contact, limited to 1024x1024px")
    image_medium = fields.Binary("Medium Image", compute="_get_image", help="This field holds the image used as avatar for this contact, limited to 1024x1024px")
    image_small = fields.Binary("Small Image", compute="_get_image", help="This field holds the image used as avatar for this contact, limited to 1024x1024px")
    model_line = fields.One2many('ksp.jaminan.model', 'merk')
    jenis = fields.Selection([
        ('mobil', 'Mobil'),
        ('motor', "Sepeda Motor"),
        ('sertifikat', 'Sertifikat'),
        ('other', 'Lain-lain'),
    ])

    @api.depends("image")
    def _get_image(self):
        for record in self:
            image = record.image
            data = tools.image_get_resized_images(image)
            record.image_medium = data["image_medium"]
            record.image_small = data["image_small"]

class KspJaminanModel(models.Model):
    _name = "ksp.jaminan.model"
    _order = "merk, name, tahun"

    name = fields.Char('Model')
    merk = fields.Many2one('ksp.jaminan.merk', 'Merk')
    tahun = fields.Char('Tahun')
    harga_pasar = fields.Integer('Harga Pasar')
    image = fields.Binary("Image", attachment=True, help="This field holds the image used as avatar for this contact, limited to 1024x1024px")
    image_medium = fields.Binary("Medium Image", compute="_get_image", help="This field holds the image used as avatar for this contact, limited to 1024x1024px")
    image_small = fields.Binary("Small Image", compute="_get_image", help="This field holds the image used as avatar for this contact, limited to 1024x1024px")

    @api.depends("image")
    def _get_image(self):
        for record in self:
            image = record.image
            data = tools.image_get_resized_images(image)
            record.image_medium = data["image_medium"]
            record.image_small = data["image_small"]

class KreditReport(models.Model):
    _name = "kredit.report"
    _auto = False

    kredit_type = fields.Many2one('ksp.kredit.type', 'Jenis Kredit', store=True)
    tanggal = fields.Date(string='Tanggal', store=True)
    tgl_cair = fields.Date(string='Tanggal Cair', store=True)
    account_cair = fields.Many2one('account.account', string='Metode Pencairan', store=True)
    partner_id = fields.Many2one('res.partner', string='Nasabah', store=True)
    pokok = fields.Integer(string='Pokok', store=True)
    bunga = fields.Integer(string='Bunga', store=True)
    tempo = fields.Integer(string='Jangka Waktu', store=True)
    angsuran = fields.Integer('Angsuran', store=True)
    rate = fields.Float(string='Suku Bunga per Bulan', store=True)

    @api.model
    def init(self):
        tools.drop_view_if_exists(self._cr, 'kredit_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW kredit_report AS (
                SELECT
                    MIN(ol.id) AS id,
                    ol.partner_id AS partner_id,
                    ol.kredit_type AS kredit_type,
                    ol.pokok AS pokok,
                    ol.rate_type AS rate_type,
                    ol.tgl_cair AS tgl_cair,
                    ol.tanggal AS tanggal,
                    ol.tempo AS tempo,
                    ol.rate AS rate,
                    ol.angsuran AS angsuran,
                    ol.bunga AS bunga
                FROM ksp_kredit ol
                GROUP BY
                    ol.partner_id,
                    ol.kredit_type,
                    ol.pokok,
                    ol.rate_type,
                    ol.tgl_cair,
                    ol.tanggal,
                    ol.tempo,
                    ol.rate,
                    ol.angsuran,
                    ol.bunga
            )
        """)

