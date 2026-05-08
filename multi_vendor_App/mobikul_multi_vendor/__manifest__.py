# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Odoo Marketplace Mobile ( Android / IOS ) App",
  "summary"              :  """This module configures your Odoo Marketplace with Odoo Mobile App for Android & iOS so your customers can now access the marketplace through their mobile phone.""",
  "category"             :  "Sales",
  "version"              :  "1.0.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "",
  "description"          :  """""",
  "live_test_url"        :  "https://mpdemo.webkul.in/Mobikul",
  "depends"              :  [
                             'mobikul',
                             'odoo_marketplace',
                            ],
  "data"                 :  [],
  "demo"                 :  [],
  "css"                  :  [],
  "js"                   :  [],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  300,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}
