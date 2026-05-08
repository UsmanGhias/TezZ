import 'package:flutter/material.dart';
import '../../../../core/api/app_config.dart';
import '../../../../core/api/mobikul_api_service.dart';
import '../../../../core/theme/app_theme.dart';

class ProductDetailScreen extends StatefulWidget {
  final int templateId;
  const ProductDetailScreen({super.key, required this.templateId});
  @override State<ProductDetailScreen> createState() => _ProductDetailScreenState();
}

class _ProductDetailScreenState extends State<ProductDetailScreen> {
  Map<String, dynamic>? _product;
  bool _loading = true, _addingCart = false;
  String? _error;
  int _qty = 1;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final d = await MobikulApi.instance.productDetail(widget.templateId);
      setState(() { _product = d; _loading = false; });
    } catch (e) { setState(() { _error = e.toString(); _loading = false; }); }
  }

  Future<void> _addToCart() async {
    final pId = _product?['productId'] ?? _product?['product_id'];
    if (pId == null) return;
    setState(() => _addingCart = true);
    try {
      await MobikulApi.instance.addToCart(pId is int ? pId : int.parse('$pId'), _qty);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Added to cart!'), backgroundColor: AppTheme.success));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e'), backgroundColor: AppTheme.accent));
    } finally { if (mounted) setState(() => _addingCart = false); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.primary,
      appBar: AppBar(title: Text(_product?['name'] ?? 'Product', style: const TextStyle(fontSize: 16))),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.accent))
          : _error != null
              ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Text(_error!, style: const TextStyle(color: AppTheme.textSecond)),
                  const SizedBox(height: 16),
                  ElevatedButton(onPressed: _load, child: const Text('Retry')),
                ]))
              : _body(),
      bottomNavigationBar: _product != null ? _addBar() : null,
    );
  }

  Widget _body() {
    final p = _product!;
    final imgs = (p['images'] as List?) ?? [];
    final mainImg = imgs.isNotEmpty ? imgs[0]['image'] ?? imgs[0] : p['image'] ?? '';
    return ListView(padding: const EdgeInsets.only(bottom: 100), children: [
      // Image
      Container(
        height: 300,
        color: AppTheme.surface,
        child: mainImg.toString().isNotEmpty
            ? Image.network(AppConfig.imageUrl(mainImg.toString()), fit: BoxFit.contain,
                errorBuilder: (_, __, ___) => const Icon(Icons.image_not_supported, color: AppTheme.textSecond, size: 80))
            : const Icon(Icons.shopping_bag_outlined, color: AppTheme.accent, size: 80),
      ),
      Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(p['name'] ?? '', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: AppTheme.textPrimary)),
        const SizedBox(height: 8),
        Row(children: [
          if (p['price'] != null) Text('Rs. ${p['price']}', style: const TextStyle(fontSize: 22, color: AppTheme.accent, fontWeight: FontWeight.w800)),
          const Spacer(),
          if (p['rating'] != null) Row(children: [
            const Icon(Icons.star, color: AppTheme.gold, size: 16),
            const SizedBox(width: 4),
            Text('${p['rating']}', style: const TextStyle(color: AppTheme.textSecond)),
          ]),
        ]),
        if (p['description'] != null) ...[
          const SizedBox(height: 16),
          const Text('Description', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
          const SizedBox(height: 6),
          Text(p['description'].toString().replaceAll(RegExp(r'<[^>]*>'), ''),
            style: const TextStyle(color: AppTheme.textSecond, height: 1.6)),
        ],
        // Qty selector
        const SizedBox(height: 24),
        Row(children: [
          const Text('Quantity:', style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600)),
          const Spacer(),
          IconButton(onPressed: () { if (_qty > 1) setState(() => _qty--); }, icon: const Icon(Icons.remove_circle_outline, color: AppTheme.accent)),
          Text('$_qty', style: const TextStyle(color: AppTheme.textPrimary, fontSize: 16, fontWeight: FontWeight.w700)),
          IconButton(onPressed: () => setState(() => _qty++), icon: const Icon(Icons.add_circle_outline, color: AppTheme.accent)),
        ]),
      ])),
    ]);
  }

  Widget _addBar() => Container(
    color: AppTheme.surface,
    padding: const EdgeInsets.fromLTRB(16, 12, 16, 20),
    child: ElevatedButton.icon(
      onPressed: _addingCart ? null : _addToCart,
      icon: _addingCart ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.shopping_cart),
      label: const Text('Add to Cart'),
    ),
  );
}
