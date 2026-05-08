import 'package:flutter/material.dart';
import '../../../../core/api/app_config.dart';
import '../../../../core/api/mobikul_api_service.dart';
import '../../../../core/theme/app_theme.dart';

class CartScreen extends StatefulWidget {
  const CartScreen({super.key});
  @override State<CartScreen> createState() => _CartScreenState();
}

class _CartScreenState extends State<CartScreen> {
  Map<String, dynamic>? _cart;
  bool _loading = true;
  String? _error;

  @override void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final d = await MobikulApi.instance.getCart();
      setState(() { _cart = d; _loading = false; });
    } catch (e) { setState(() { _error = e.toString(); _loading = false; }); }
  }

  @override
  Widget build(BuildContext context) {
    final lines = (_cart?['orderLines'] as List?) ?? (_cart?['cart_lines'] as List?) ?? [];
    return Scaffold(
      backgroundColor: AppTheme.primary,
      appBar: AppBar(title: const Text('My Cart')),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.accent))
          : _error != null
              ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                  const Icon(Icons.wifi_off_rounded, size: 60, color: AppTheme.textSecond),
                  const SizedBox(height: 12),
                  Text(_error!, style: const TextStyle(color: AppTheme.textSecond)),
                  const SizedBox(height: 16),
                  ElevatedButton(onPressed: _load, child: const Text('Retry')),
                ]))
              : lines.isEmpty
                  ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                      const Icon(Icons.shopping_cart_outlined, size: 80, color: AppTheme.textSecond),
                      const SizedBox(height: 16),
                      const Text('Your cart is empty', style: TextStyle(color: AppTheme.textSecond, fontSize: 16)),
                    ]))
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: Column(children: [
                        Expanded(child: ListView.builder(
                          padding: const EdgeInsets.all(12),
                          itemCount: lines.length,
                          itemBuilder: (ctx, i) => _lineCard(lines[i]),
                        )),
                        _summary(),
                      ]),
                    ),
    );
  }

  Widget _lineCard(Map l) {
    final img = l['productImage'] ?? l['image'] ?? '';
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        leading: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: img.isNotEmpty
              ? Image.network(AppConfig.imageUrl(img), width: 56, height: 56, fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(width: 56, height: 56, color: AppTheme.cardBg, child: const Icon(Icons.image, color: AppTheme.textSecond)))
              : Container(width: 56, height: 56, color: AppTheme.cardBg, child: const Icon(Icons.shopping_bag_outlined, color: AppTheme.accent)),
        ),
        title: Text(l['productName'] ?? l['name'] ?? '', style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13), maxLines: 2),
        subtitle: Text('Qty: ${l['qty'] ?? l['quantity'] ?? 1}  |  Rs. ${l['price'] ?? l['priceTotal'] ?? 0}',
          style: const TextStyle(color: AppTheme.textSecond, fontSize: 12)),
        trailing: IconButton(
          icon: const Icon(Icons.delete_outline, color: AppTheme.accent, size: 20),
          onPressed: () async {
            final lineId = l['lineId'] ?? l['id'];
            if (lineId != null) {
              await MobikulApi.instance.removeCartLine(lineId is int ? lineId : int.parse('$lineId'));
              _load();
            }
          },
        ),
      ),
    );
  }

  Widget _summary() {
    final total = _cart?['amountTotal'] ?? _cart?['total'] ?? 0;
    return Container(
      color: AppTheme.surface,
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
      child: Column(children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          const Text('Total', style: TextStyle(color: AppTheme.textPrimary, fontSize: 16, fontWeight: FontWeight.w700)),
          Text('Rs. $total', style: const TextStyle(color: AppTheme.accent, fontSize: 18, fontWeight: FontWeight.w800)),
        ]),
        const SizedBox(height: 14),
        SizedBox(width: double.infinity, child: ElevatedButton(onPressed: () {}, child: const Text('Checkout'))),
      ]),
    );
  }
}
