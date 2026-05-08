import 'package:flutter/material.dart';
import '../../../../core/api/app_config.dart';
import '../../../../core/api/mobikul_api_service.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/app_router.dart';

class ShopScreen extends StatefulWidget {
  const ShopScreen({super.key});
  @override State<ShopScreen> createState() => _ShopScreenState();
}

class _ShopScreenState extends State<ShopScreen> {
  List _products = [];
  bool _loading = true;
  String? _error;
  int _offset = 0;
  static const int _limit = 20;
  bool _hasMore = true;
  final _scroll = ScrollController();

  @override
  void initState() {
    super.initState();
    _load();
    _scroll.addListener(_onScroll);
  }

  @override
  void dispose() { _scroll.dispose(); super.dispose(); }

  void _onScroll() {
    if (_scroll.position.pixels > _scroll.position.maxScrollExtent - 200 && _hasMore && !_loading) {
      _loadMore();
    }
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; _offset = 0; _products = []; _hasMore = true; });
    try {
      final d = await MobikulApi.instance.searchProducts(offset: 0, limit: _limit);
      final list = (d['products'] as List?) ?? (d['productList'] as List?) ?? [];
      setState(() { _products = list; _loading = false; _offset = list.length; _hasMore = list.length == _limit; });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  Future<void> _loadMore() async {
    if (!_hasMore || _loading) return;
    setState(() => _loading = true);
    try {
      final d = await MobikulApi.instance.searchProducts(offset: _offset, limit: _limit);
      final list = (d['products'] as List?) ?? (d['productList'] as List?) ?? [];
      setState(() {
        _products = [..._products, ...list];
        _offset += list.length;
        _hasMore = list.length == _limit;
        _loading = false;
      });
    } catch (_) { setState(() => _loading = false); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.primary,
      appBar: AppBar(
        title: const Text('Shop'),
        actions: [IconButton(icon: const Icon(Icons.search), onPressed: () => Navigator.pushNamed(context, AppRouter.search))],
      ),
      body: _error != null && _products.isEmpty
          ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Icon(Icons.wifi_off_rounded, size: 60, color: AppTheme.textSecond),
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: AppTheme.textSecond), textAlign: TextAlign.center),
              const SizedBox(height: 16),
              ElevatedButton(onPressed: _load, child: const Text('Retry')),
            ]))
          : RefreshIndicator(
              onRefresh: _load,
              child: _products.isEmpty && _loading
                  ? const Center(child: CircularProgressIndicator(color: AppTheme.accent))
                  : GridView.builder(
                      controller: _scroll,
                      padding: const EdgeInsets.all(12),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2, childAspectRatio: 0.72, crossAxisSpacing: 10, mainAxisSpacing: 10,
                      ),
                      itemCount: _products.length + (_hasMore ? 1 : 0),
                      itemBuilder: (ctx, i) {
                        if (i == _products.length) return const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator(color: AppTheme.accent)));
                        return _productCard(_products[i]);
                      },
                    ),
            ),
    );
  }

  Widget _productCard(Map p) {
    final id  = p['id'] ?? p['template_id'] ?? 0;
    final img = p['image'] ?? p['image_url'] ?? '';
    return GestureDetector(
      onTap: () => Navigator.pushNamed(context, AppRouter.productDetail, arguments: id is int ? id : int.tryParse('$id') ?? 0),
      child: Container(
        decoration: BoxDecoration(color: AppTheme.surface, borderRadius: BorderRadius.circular(16)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(child: ClipRRect(
            borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
            child: img.isNotEmpty
                ? Image.network(AppConfig.imageUrl(img), fit: BoxFit.cover, width: double.infinity,
                    errorBuilder: (_, __, ___) => Container(color: AppTheme.cardBg, child: const Icon(Icons.image_not_supported, color: AppTheme.textSecond)))
                : Container(color: AppTheme.cardBg, child: const Icon(Icons.shopping_bag_outlined, color: AppTheme.accent, size: 40)),
          )),
          Padding(padding: const EdgeInsets.all(10), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(p['name'] ?? '', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textPrimary), maxLines: 2, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 4),
            Text(p['price'] != null ? 'Rs. ${p['price']}' : '', style: const TextStyle(fontSize: 13, color: AppTheme.accent, fontWeight: FontWeight.w700)),
          ])),
        ]),
      ),
    );
  }
}
