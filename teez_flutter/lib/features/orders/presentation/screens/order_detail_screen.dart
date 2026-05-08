import 'package:flutter/material.dart';
import '../../../../core/api/mobikul_api_service.dart';
import '../../../../core/theme/app_theme.dart';

class OrderDetailScreen extends StatefulWidget {
  final int orderId;
  const OrderDetailScreen({super.key, required this.orderId});
  @override State<OrderDetailScreen> createState() => _OrderDetailScreenState();
}

class _OrderDetailScreenState extends State<OrderDetailScreen> {
  Map<String, dynamic>? _order;
  bool _loading = true;
  String? _error;

  @override void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final d = await MobikulApi.instance.orderDetail(widget.orderId);
      setState(() { _order = d; _loading = false; });
    } catch (e) { setState(() { _error = e.toString(); _loading = false; }); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.primary,
      appBar: AppBar(title: Text('Order #${_order?['name'] ?? widget.orderId}')),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.accent))
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: AppTheme.textSecond)))
              : _body(),
    );
  }

  Widget _body() {
    final o = _order!;
    final lines = (o['orderLines'] as List?) ?? [];
    return ListView(padding: const EdgeInsets.all(16), children: [
      _row('Order', o['name'] ?? '${o['id']}'),
      _row('Date', o['date_order'] ?? o['dateOrder'] ?? ''),
      _row('Status', o['state'] ?? ''),
      _row('Total', 'Rs. ${o['amount_total'] ?? o['amountTotal'] ?? 0}'),
      const SizedBox(height: 20),
      const Text('Items', style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w700, fontSize: 16)),
      const SizedBox(height: 8),
      ...lines.map((l) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(children: [
          Expanded(child: Text(l['name'] ?? l['productName'] ?? '', style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13))),
          Text('x${l['qty'] ?? l['productQuantity'] ?? 1}', style: const TextStyle(color: AppTheme.textSecond, fontSize: 12)),
          const SizedBox(width: 12),
          Text('Rs. ${l['price'] ?? l['priceTotal'] ?? 0}', style: const TextStyle(color: AppTheme.accent, fontSize: 13, fontWeight: FontWeight.w600)),
        ]),
      )),
    ]);
  }

  Widget _row(String k, String v) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 6),
    child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
      Text(k, style: const TextStyle(color: AppTheme.textSecond)),
      Text(v, style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600)),
    ]),
  );
}
