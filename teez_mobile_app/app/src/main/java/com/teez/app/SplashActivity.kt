package com.teez.app

import android.content.Intent
import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import com.teez.app.databinding.ActivitySplashBinding

class SplashActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySplashBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySplashBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Login button → open Odoo login page
        binding.btnLogin.setOnClickListener {
            openMain(AppConfig.LOGIN_URL)
        }

        // Sign Up button → open Odoo registration page
        binding.btnSignup.setOnClickListener {
            openMain(AppConfig.SIGNUP_URL)
        }

        // Browse as guest
        binding.btnGuest.setOnClickListener {
            openMain(AppConfig.HOME_URL)
        }
    }

    private fun openMain(url: String) {
        val intent = Intent(this, MainActivity::class.java)
        intent.putExtra(MainActivity.EXTRA_URL, url)
        startActivity(intent)
        overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out)
    }
}
