import 'package:flutter/material.dart';
import '../../features/splash/presentation/screens/splash_screen.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/auth/presentation/screens/signup_screen.dart';
import '../../features/shell/main_shell.dart';
import '../../features/shop/presentation/screens/product_detail_screen.dart';
import '../../features/orders/presentation/screens/orders_screen.dart';
import '../../features/orders/presentation/screens/order_detail_screen.dart';
import '../../features/wishlist/presentation/screens/wishlist_screen.dart';
import '../../features/search/presentation/screens/search_screen.dart';

class AppRouter {
  static const String splash        = '/';
  static const String login         = '/login';
  static const String signup        = '/signup';
  static const String home          = '/home';
  static const String productDetail = '/product';
  static const String orders        = '/orders';
  static const String orderDetail   = '/order-detail';
  static const String wishlist      = '/wishlist';
  static const String search        = '/search';

  static Route<dynamic> generateRoute(RouteSettings s) {
    switch (s.name) {
      case splash:        return _page(const SplashScreen(), s);
      case login:         return _page(const LoginScreen(), s);
      case signup:        return _page(const SignupScreen(), s);
      case home:          return _page(const MainShell(), s);
      case orders:        return _page(const OrdersScreen(), s);
      case wishlist:      return _page(const WishlistScreen(), s);
      case search:
        final q = s.arguments as String?;
        return _page(SearchScreen(initialQuery: q), s);
      case productDetail:
        final id = s.arguments as int;
        return _page(ProductDetailScreen(templateId: id), s);
      case orderDetail:
        final id = s.arguments as int;
        return _page(OrderDetailScreen(orderId: id), s);
      default:            return _page(const SplashScreen(), s);
    }
  }

  static PageRoute _page(Widget w, RouteSettings s) =>
      MaterialPageRoute(builder: (_) => w, settings: s);
}
