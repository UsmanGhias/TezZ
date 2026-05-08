package com.teez.app

/**
 * Central configuration for Teez app URLs.
 *
 * Emulator  → 10.0.2.2:8069       (maps to host localhost)
 * LAN/Phone → 192.168.100.252:8069  (same WiFi)
 * Cloudflare→ https://xxx.trycloudflare.com  (public, rebuild when needed)
 */
object AppConfig {
    // LAN IP — device must be on the same WiFi as the Odoo server
    const val HOST = "http://192.168.100.252:8069"

    const val HOME_URL    = "$HOST/"
    const val SHOP_URL    = "$HOST/shop"
    const val CART_URL    = "$HOST/shop/cart"
    const val ORDERS_URL  = "$HOST/my/orders"
    const val LOGIN_URL   = "$HOST/web/login"
    const val SIGNUP_URL  = "$HOST/web/signup"
    const val ACCOUNT_URL = "$HOST/my/account"
}
