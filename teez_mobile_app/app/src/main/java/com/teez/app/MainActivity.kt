package com.teez.app

import android.annotation.SuppressLint
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.KeyEvent
import android.view.View
import android.webkit.*
import android.widget.ProgressBar
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.teez.app.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_URL = "extra_url"
    }

    private lateinit var binding: ActivityMainBinding
    private lateinit var webView: WebView

    // Track the tab that is currently "active" so we can re-select it
    private var activeNavId = R.id.nav_home

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        webView = binding.webView

        // ── WebView settings ────────────────────────────────────────────────
        webView.settings.apply {
            javaScriptEnabled          = true
            domStorageEnabled          = true
            loadWithOverviewMode       = true
            useWideViewPort            = true
            setSupportZoom(false)
            builtInZoomControls        = false
            displayZoomControls        = false
            databaseEnabled            = true
            allowFileAccess            = true
            javaScriptCanOpenWindowsAutomatically = true
            mixedContentMode           = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            cacheMode                  = WebSettings.LOAD_DEFAULT
            userAgentString            = "TeezApp/1.0 ${userAgentString}"
        }

        // ── WebViewClient ───────────────────────────────────────────────────
        webView.webViewClient = object : WebViewClient() {
            override fun onPageStarted(view: WebView?, url: String?, favicon: android.graphics.Bitmap?) {
                binding.progressBar.visibility = View.VISIBLE
            }
            override fun onPageFinished(view: WebView?, url: String?) {
                binding.progressBar.visibility = View.GONE
                syncNavWithUrl(url)
            }
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url.toString()
                // Keep ALL navigation inside the WebView — never open Chrome
                // Only hard-skip truly external schemes (mailto, tel, etc.)
                return when {
                    url.startsWith("mailto:") || url.startsWith("tel:") || url.startsWith("intent:") -> {
                        try { startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url))) } catch (_: Exception) {}
                        true
                    }
                    else -> {
                        view.loadUrl(url)
                        true
                    }
                }
            }
            override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: WebResourceError?) {
                // Only show error for main frame
                if (request?.isForMainFrame == true) {
                    view?.loadData(
                        buildErrorPage(error?.description.toString()),
                        "text/html", "UTF-8"
                    )
                }
            }
        }

        // ── WebChromeClient (progress + file chooser) ───────────────────────
        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                binding.progressBar.progress = newProgress
            }
        }

        // ── Bottom Navigation ───────────────────────────────────────────────
        binding.bottomNav.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_home    -> { loadUrl(AppConfig.HOME_URL);    activeNavId = item.itemId; true }
                R.id.nav_shop    -> { loadUrl(AppConfig.SHOP_URL);    activeNavId = item.itemId; true }
                R.id.nav_cart    -> { loadUrl(AppConfig.CART_URL);    activeNavId = item.itemId; true }
                R.id.nav_orders  -> { loadUrl(AppConfig.ORDERS_URL);  activeNavId = item.itemId; true }
                R.id.nav_account -> { loadUrl(AppConfig.ACCOUNT_URL); activeNavId = item.itemId; true }
                else -> false
            }
        }

        // ── Initial URL ─────────────────────────────────────────────────────
        val startUrl = intent.getStringExtra(EXTRA_URL) ?: AppConfig.HOME_URL
        loadUrl(startUrl)
        syncNavWithUrl(startUrl)

        // Restore saved state (e.g. on rotation)
        savedInstanceState?.let { webView.restoreState(it) }
    }

    private fun loadUrl(url: String) {
        if (webView.url != url) {
            webView.loadUrl(url)
        }
    }

    /** Highlight the correct bottom-nav item based on current URL. */
    private fun syncNavWithUrl(url: String?) {
        if (url == null) return
        val id = when {
            url.contains("/shop/cart")  -> R.id.nav_cart
            url.contains("/shop")       -> R.id.nav_shop
            url.contains("/my/orders")  -> R.id.nav_orders
            url.contains("/my/")        -> R.id.nav_account
            else                        -> R.id.nav_home
        }
        if (id != activeNavId) {
            activeNavId = id
            binding.bottomNav.selectedItemId = id
        }
    }

    private fun buildErrorPage(msg: String) = """
        <html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="font-family:'Segoe UI',sans-serif;padding:40px 24px;text-align:center;background:#0f0f14;color:#f0f0f0;">
        <h2 style="color:#c0392b">Connection Error</h2>
        <p>Could not connect to the Teez server.</p>
        <p style="color:#7f8c8d;font-size:13px">$msg</p>
        <p>Make sure the Odoo server is running on port 8069.</p>
        <button onclick="location.reload()" style="padding:12px 24px;background:#2980b9;color:#fff;border:none;border-radius:6px;font-size:16px">
            Retry
        </button></body></html>
    """.trimIndent()

    // ── Hardware back key ────────────────────────────────────────────────────
    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack()
            return true
        }
        return super.onKeyDown(keyCode, event)
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        webView.saveState(outState)
    }
}
