import 'package:flutter/material.dart';
import '../../../../core/api/mobikul_api_service.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/app_router.dart';

class AccountScreen extends StatefulWidget {
  const AccountScreen({super.key});
  @override State<AccountScreen> createState() => _AccountScreenState();
}

class _AccountScreenState extends State<AccountScreen> {
  bool _loggedIn = false;
  String _name = 'Guest';
  String _email = '';

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    _loggedIn = await MobikulApi.isLoggedIn;
    _name     = await MobikulApi.userName;
    _email    = await MobikulApi.userEmail;
    if (mounted) setState(() {});
  }

  Future<void> _logout() async {
    await MobikulApi.instance.signOut();
    if (mounted) Navigator.pushReplacementNamed(context, AppRouter.login);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.primary,
      appBar: AppBar(title: const Text('Account')),
      body: ListView(padding: const EdgeInsets.all(20), children: [
        // Avatar
        Center(child: Column(children: [
          Container(
            width: 80, height: 80,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(colors: [AppTheme.accent, AppTheme.gold], begin: Alignment.topLeft, end: Alignment.bottomRight),
            ),
            child: Center(child: Text(_name.isNotEmpty ? _name[0].toUpperCase() : 'G',
              style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w800, color: Colors.white))),
          ),
          const SizedBox(height: 12),
          Text(_name, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppTheme.textPrimary)),
          if (_email.isNotEmpty) Text(_email, style: const TextStyle(color: AppTheme.textSecond, fontSize: 13)),
        ])),
        const SizedBox(height: 32),
        if (_loggedIn) ...[
          _tile(Icons.receipt_long_outlined, 'My Orders', () => Navigator.pushNamed(context, AppRouter.orders)),
          _tile(Icons.favorite_outline, 'Wishlist', () => Navigator.pushNamed(context, AppRouter.wishlist)),
          _tile(Icons.location_on_outlined, 'Addresses', () {}),
          _tile(Icons.support_agent_outlined, 'Support', () {}),
          const Divider(color: AppTheme.surface, height: 32),
          _tile(Icons.logout, 'Sign Out', _logout, color: AppTheme.accent),
        ] else ...[
          ElevatedButton(onPressed: () => Navigator.pushNamed(context, AppRouter.login), child: const Text('Sign In')),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: () => Navigator.pushNamed(context, AppRouter.signup),
            style: OutlinedButton.styleFrom(side: const BorderSide(color: AppTheme.accent), foregroundColor: AppTheme.accent,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            child: const Text('Create Account'),
          ),
          const SizedBox(height: 24),
          _tile(Icons.receipt_long_outlined, 'My Orders', () => Navigator.pushNamed(context, AppRouter.orders)),
          _tile(Icons.favorite_outline, 'Wishlist', () => Navigator.pushNamed(context, AppRouter.wishlist)),
        ],
      ]),
    );
  }

  Widget _tile(IconData icon, String label, VoidCallback onTap, {Color? color}) => ListTile(
    contentPadding: const EdgeInsets.symmetric(vertical: 4),
    leading: Icon(icon, color: color ?? AppTheme.accent),
    title: Text(label, style: TextStyle(color: color ?? AppTheme.textPrimary, fontWeight: FontWeight.w500)),
    trailing: const Icon(Icons.chevron_right, color: AppTheme.textSecond, size: 18),
    onTap: onTap,
  );
}
