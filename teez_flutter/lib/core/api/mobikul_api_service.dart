import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'app_config.dart';

class ApiError implements Exception {
  final String message;
  ApiError(this.message);
  @override String toString() => message;
}

class MobikulApi {
  static MobikulApi? _instance;
  static MobikulApi get instance => _instance ??= MobikulApi._();
  MobikulApi._();

  // ── Dio instance ────────────────────────────────────────────────────────────
  Dio get _dio => Dio(BaseOptions(
    baseUrl: AppConfig.baseUrl,
    connectTimeout: Duration(seconds: AppConfig.connectTimeoutSec),
    receiveTimeout: Duration(seconds: AppConfig.receiveTimeoutSec),
    headers: _baseHeaders(),
  ));

  // ── Helpers ─────────────────────────────────────────────────────────────────
  Map<String, String> _baseHeaders({String? login, String? pwd}) {
    // Basic Auth with API key
    final creds = base64Encode(utf8.encode('customer:${AppConfig.apiKey}'));
    final h = <String, String>{
      'Authorization': 'Basic $creds',
      'Content-Type': 'application/json',
    };
    if (login != null && pwd != null) {
      final loginB64 = base64Encode(utf8.encode("{'login': '$login', 'pwd': '$pwd'}"));
      h['Login'] = loginB64;
    }
    return h;
  }

  Future<Map<String, String>> _authHeaders() async {
    final p = await SharedPreferences.getInstance();
    final login = p.getString('user_email') ?? '';
    final pwd   = p.getString('user_pwd')   ?? '';
    if (login.isEmpty || pwd.isEmpty) return _baseHeaders();
    return _baseHeaders(login: login, pwd: pwd);
  }

  Map<String, dynamic> _ok(Response r) {
    final data = r.data;
    if (data is Map<String, dynamic>) return data;
    if (data is String) {
      try { return jsonDecode(data); } catch (_) {}
    }
    return {};
  }

  void _checkSuccess(Map<String, dynamic> data) {
    if (data['success'] == false) {
      throw ApiError(data['message'] ?? 'Request failed');
    }
  }

  // ── Public methods ───────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> splashData() async {
    final r = await _dio.post(AppConfig.splashData, data: {});
    return _ok(r);
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final headers = _baseHeaders(login: email, pwd: password);
    final r = await _dio.post(
      AppConfig.loginEndpoint,
      data: {'login': email, 'password': password},
      options: Options(headers: headers),
    );
    final data = _ok(r);
    _checkSuccess(data);
    // Save credentials
    final p = await SharedPreferences.getInstance();
    await p.setString('user_email', email);
    await p.setString('user_pwd', password);
    await p.setBool('is_logged_in', true);
    await p.setString('user_name', data['name'] ?? '');
    await p.setInt('customer_id', (data['customerId'] ?? 0) as int);
    await p.setString('user_token', data['token'] ?? '');
    return data;
  }

  Future<Map<String, dynamic>> signUp({
    required String name,
    required String email,
    required String password,
  }) async {
    final r = await _dio.post(
      AppConfig.signUpEndpoint,
      data: {'name': name, 'login': email, 'password': password, 'confirmPassword': password},
    );
    final data = _ok(r);
    _checkSuccess(data);
    return data;
  }

  Future<void> signOut() async {
    try {
      final headers = await _authHeaders();
      await _dio.post(AppConfig.signOut, data: {}, options: Options(headers: headers));
    } catch (_) {}
    final p = await SharedPreferences.getInstance();
    await p.clear();
  }

  Future<Map<String, dynamic>> homepage() async {
    final headers = await _authHeaders();
    final r = await _dio.post(AppConfig.homepage, data: {}, options: Options(headers: headers));
    return _ok(r);
  }

  Future<Map<String, dynamic>> searchProducts({
    String? keyword,
    int? categoryId,
    int offset = 0,
    int limit = 20,
    String order = 'id desc',
    double? minPrice,
    double? maxPrice,
  }) async {
    final headers = await _authHeaders();
    final body = <String, dynamic>{
      'offset': offset,
      'limit': limit,
      'order': order,
    };
    if (keyword != null && keyword.isNotEmpty) body['keyword'] = keyword;
    if (categoryId != null) body['category_id'] = categoryId;
    if (minPrice != null) body['min_price'] = minPrice;
    if (maxPrice != null) body['max_price'] = maxPrice;
    final r = await _dio.post(AppConfig.search, data: body, options: Options(headers: headers));
    return _ok(r);
  }

  Future<Map<String, dynamic>> productDetail(int templateId) async {
    final headers = await _authHeaders();
    final r = await _dio.post(
      AppConfig.templateUrl(templateId),
      data: {},
      options: Options(headers: headers),
    );
    return _ok(r);
  }

  Future<Map<String, dynamic>> getCart() async {
    final headers = await _authHeaders();
    final r = await _dio.post(AppConfig.mycart, data: {}, options: Options(headers: headers));
    return _ok(r);
  }

  Future<Map<String, dynamic>> addToCart(int productId, int qty) async {
    final headers = await _authHeaders();
    final r = await _dio.post(
      AppConfig.addToCart,
      data: {'product_id': productId, 'qty': qty},
      options: Options(headers: headers),
    );
    return _ok(r);
  }

  Future<Map<String, dynamic>> updateCartLine(int lineId, int qty) async {
    final headers = await _authHeaders();
    final r = await _dio.put(
      '${AppConfig.mycart}/$lineId',
      data: {'qty': qty},
      options: Options(headers: headers),
    );
    return _ok(r);
  }

  Future<Map<String, dynamic>> removeCartLine(int lineId) async {
    final headers = await _authHeaders();
    final r = await _dio.delete(
      '${AppConfig.mycart}/$lineId',
      data: {},
      options: Options(headers: headers),
    );
    return _ok(r);
  }

  Future<Map<String, dynamic>> myOrders({int offset = 0, int limit = 20}) async {
    final headers = await _authHeaders();
    final r = await _dio.post(
      AppConfig.myOrders,
      data: {'offset': offset, 'limit': limit},
      options: Options(headers: headers),
    );
    return _ok(r);
  }

  Future<Map<String, dynamic>> orderDetail(int orderId) async {
    final headers = await _authHeaders();
    final r = await _dio.post(
      AppConfig.orderUrl(orderId),
      data: {},
      options: Options(headers: headers),
    );
    return _ok(r);
  }

  Future<Map<String, dynamic>> myAccount() async {
    final headers = await _authHeaders();
    final r = await _dio.post(AppConfig.myAccount, data: {}, options: Options(headers: headers));
    return _ok(r);
  }

  Future<Map<String, dynamic>> getWishlists() async {
    final headers = await _authHeaders();
    final r = await _dio.post(AppConfig.wishlists, data: {}, options: Options(headers: headers));
    return _ok(r);
  }

  Future<void> addToWishlist(int productId) async {
    final headers = await _authHeaders();
    await _dio.post(AppConfig.addWishlist, data: {'product_id': productId}, options: Options(headers: headers));
  }

  Future<void> removeFromWishlist(int productId) async {
    final headers = await _authHeaders();
    await _dio.delete('${AppConfig.removeWishlist}/$productId', data: {}, options: Options(headers: headers));
  }

  Future<Map<String, dynamic>> getReviews(int templateId) async {
    final r = await _dio.post(AppConfig.reviews, data: {'template_id': templateId});
    return _ok(r);
  }

  Future<Map<String, dynamic>> sellerProfile(int sellerId) async {
    final r = await _dio.get(AppConfig.sellerUrl(sellerId));
    return _ok(r);
  }

  Future<Map<String, dynamic>> marketplace({int offset = 0}) async {
    final r = await _dio.get(
      AppConfig.marketplace,
      queryParameters: {'offset': offset},
    );
    return _ok(r);
  }

  // ── Helpers ─────────────────────────────────────────────────────────────────
  static Future<bool> get isLoggedIn async {
    final p = await SharedPreferences.getInstance();
    return p.getBool('is_logged_in') ?? false;
  }

  static Future<String> get userName async {
    final p = await SharedPreferences.getInstance();
    return p.getString('user_name') ?? 'Guest';
  }

  static Future<String> get userEmail async {
    final p = await SharedPreferences.getInstance();
    return p.getString('user_email') ?? '';
  }

  static Future<int> get customerId async {
    final p = await SharedPreferences.getInstance();
    return p.getInt('customer_id') ?? 0;
  }
}
