class AppConfig {
  static const String baseUrl     = 'http://192.168.100.252:8069';
  static const String apiKey      = '4495-bfaa-90d85dfa1773';
  static const int    connectTimeoutSec = 15;
  static const int    receiveTimeoutSec = 30;

  // Endpoints
  static const String splashData      = '/mobikul/splashPageData';
  static const String loginEndpoint   = '/mobikul/customer/login';
  static const String signUpEndpoint  = '/mobikul/customer/signUp';
  static const String signOut         = '/mobikul/customer/logout';
  static const String homepage        = '/mobikul/homepage';
  static const String search          = '/mobikul/search';
  static const String mycart          = '/mobikul/mycart';
  static const String addToCart       = '/mobikul/mycart/addToCart';
  static const String myOrders        = '/mobikul/my/orders';
  static const String myAccount       = '/mobikul/my/account';
  static const String wishlists       = '/mobikul/my/wishlists';
  static const String addWishlist     = '/mobikul/my/wishlist/add';
  static const String removeWishlist  = '/mobikul/my/wishlist/remove';
  static const String reviews         = '/mobikul/reviews';
  static const String marketplace     = '/marketplace/sellers';

  // Dynamic
  static String templateUrl(int id)  => '/mobikul/template/$id';
  static String orderUrl(int id)     => '/mobikul/my/order/$id';
  static String sellerUrl(int id)    => '/marketplace/seller/$id';
  static String imageUrl(String path) => '$baseUrl$path';
}
