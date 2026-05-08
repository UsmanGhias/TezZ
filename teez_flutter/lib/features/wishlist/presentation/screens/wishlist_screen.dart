import 'package:flutter/material.dart';
import '../../../../core/api/app_config.dart';
import '../../../../core/api/mobikul_api_service.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/app_router.dart';

class WishlistScreen extends StatefulWidget {
  const WishlistScreen({super.key});
  @override State<WishlistScreen> createState() => _WishlistScreenState();
}

class _WishlistScreenState extends State<WishlistScreen> {
  List _items = [];
  bool _loading = true;
  String? _error;

  @override void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final d = await MobikulApi.instance.getWishlists();
      setState(() { _items = (d['wishlistItems'] as List?) ?? (d['wishlists'] as List?) ?? []; _loading = false; });
    } catch (e) { setState(() { _error = e.toString(); _loading = false; }); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.primary,
      appBar: AppBar(title: const Text('Wishlist')),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.accent))
          : _error != null
              ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Text(_error!, style: const TextStyle(color: AppTheme.textSecond), textAlign: TextAlign.center),
                  const SizedBox(height: 16),
                  ElevatedButton(onPressed: _load, child: const Text('Retry')),
                ]))
              : _items.isEmpty
                  ? const Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                      Icon(Icons.favorite_border, size: 80, color: AppTheme.textSecond),
                      SizedBox(height: 16),
                      Text('No items in wishlist', style: TextStyle(color: AppTheme.textSecond, fontSize: 16)),
                    ]))
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: GridView.builder(
                        padding: const EdgeInsets.all(12),
                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 2, childAspectRatio: 0.72, crossAxisSpacing: 10, mainAxisSpacing: 10,
                        ),
                        itemCount: _items.length,
                        itemBuilder: (ctx, i) => _card(_items[i]),
                      ),
                    ),
    );
  }

  Widget _card(Map p) {
    final id  = p['template_id'] ?? p['id'] ?? 0;
    final img = p['image'] ?? '';
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
