# -*- coding: utf-8 -*-
#############################################################################
#
#    ALFAWEB.vn.
#
#    Copyright (C) 2020 ALFAWEB.vn(<http://ALFAWEB.vn)
#    Author: ALFAWEB.vn (<http://ALFAWEB.vn)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Filtre Partenaires par client ou fournisseur',
    'version': '14.0.0.0.1',
    'category': 'Accounting',
    'author': 'Mohammed Amine EL ARABI',
    'website': 'http://www.s2g-ti.ma',
    'summary': 'Partenaire Filtrer par client ou fournisseur',
    'images': ["static/description/icon.png"],
    'depends': [
        'account',
        'base',
        'sale',
        'purchase',
    ],
    'data': [
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
